import asyncio
import datetime
import random
from typing import Optional, List, Dict, Any, Callable
from sqlmodel import Session, select
from backend.database import engine, Account, Proxy, Campaign, TaskItem, ExecutionLog
from backend.core.proxy_rotator import ProxyManager, AutoProxyEngine
from backend.core.browser_pool import browser_pool
from backend.core.daraz_bot import DarazBotEngine
from backend.config import settings

class CampaignRunner:
    def __init__(self, campaign_id: int, broadcast_callback: Optional[Callable] = None):
        self.campaign_id = campaign_id
        self.broadcast = broadcast_callback
        self.is_running = False
        self.stop_requested = False
        self.task: Optional[asyncio.Task] = None

    async def log(self, level: str, message: str, account_email: Optional[str] = None):
        try:
            print(f"[{level.upper()}] [Campaign {self.campaign_id}] {message}")
        except Exception:
            try:
                print(f"[{level.upper()}] [Campaign {self.campaign_id}] {message.encode('ascii', 'ignore').decode('ascii')}")
            except Exception:
                pass
        try:
            with Session(engine) as session:
                db_log = ExecutionLog(
                    campaign_id=self.campaign_id,
                    account_email=account_email,
                    level=level,
                    message=message,
                    timestamp=datetime.datetime.utcnow()
                )
                session.add(db_log)
                session.commit()
        except Exception:
            pass
            
        if self.broadcast:
            try:
                await self.broadcast({
                    "type": "log",
                    "campaign_id": self.campaign_id,
                    "account_email": account_email,
                    "level": level,
                    "message": message,
                    "timestamp": datetime.datetime.utcnow().isoformat()
                })
            except Exception:
                pass

    def get_campaign(self, session: Session) -> Optional[Campaign]:
        return session.get(Campaign, self.campaign_id)

    def get_next_available_account(self, session: Session) -> Optional[Account]:
        """Finds the next ready account with available daily order quota."""
        now = datetime.datetime.utcnow()
        # Reset daily counters if last used was more than 24 hours ago
        accounts = session.exec(select(Account)).all()
        for acc in accounts:
            if acc.last_used_at and (now - acc.last_used_at).total_seconds() > 86400:
                acc.daily_orders_count = 0
                if acc.status == "cooldown":
                    acc.status = "active"
                session.add(acc)
        session.commit()

        # Query active ready account ordered by least recently used (Round-Robin Fair Rotation)
        statement = select(Account).where(
            Account.status == "active",
            Account.daily_orders_count < Account.max_daily_orders
        ).order_by(Account.last_used_at.asc().nullsfirst())
        return session.exec(statement).first()

    def get_active_proxy(self, session: Session) -> Optional[Proxy]:
        return session.exec(select(Proxy).where(Proxy.is_active == True)).first()

    async def run(self):
        self.is_running = True
        self.stop_requested = False
        
        with Session(engine) as session:
            campaign = self.get_campaign(session)
            if not campaign:
                self.is_running = False
                return
            campaign.status = "running"
            session.add(campaign)
            session.commit()
            
            c_name = campaign.name
            c_target_orders = campaign.target_orders_count
            c_target_atc = campaign.target_atc_count

        await self.log("info", f"Started Campaign: '{c_name}' | Target Orders: {c_target_orders} | Target ATC: {c_target_atc}")

        try:
            while not self.stop_requested:
                with Session(engine) as session:
                    campaign = self.get_campaign(session)
                    if not campaign or campaign.status != "running" or self.stop_requested:
                        break
                        
                    # Check campaign mode
                    c_type = campaign.campaign_type or "atc_rank_boost"
                    
                    # --- MODE 1: ATC & ORGANIC RANK BOOSTER (Solution 4 - Infinite Traffic & ATC) ---
                    if c_type == "atc_rank_boost":
                        atc_done = campaign.completed_atc_count >= campaign.target_atc_count
                        wishlist_done = campaign.completed_wishlist_count >= campaign.target_wishlist_count
                        
                        if atc_done and wishlist_done:
                            campaign.status = "completed"
                            session.add(campaign)
                            session.commit()
                            await self.log("success", f"🎯 Solution 4 Rank Boost Finished! Successfully completed {campaign.completed_atc_count} Add-To-Carts for '{campaign.name}'!")
                            break

                        # Solution 4: Always use an isolated, unique anti-detect stealth session per cycle
                        acc_email = f"stealth_ranker_{campaign.id}_{random.randint(10000, 99999)}@daraz.pk"
                        acc_password = None
                        acc_phone = None
                        acc_id = None
                        action_to_do = "add_to_cart"

                    # --- MODE 2: DEDICATED SELF-ORDER CHECKOUT (1 Order Per ID Per Day) ---
                    else:
                        if campaign.completed_orders_count >= campaign.target_orders_count:
                            campaign.status = "completed"
                            session.add(campaign)
                            session.commit()
                            await self.log("success", f"🛒 Self-Order Campaign Finished! Completed {campaign.completed_orders_count}/{campaign.target_orders_count} orders.")
                            break

                        account = self.get_next_available_account(session)
                        if not account:
                            await self.log("warning", "All available accounts in pool have placed their 1 order for today! Pausing campaign to protect accounts.")
                            campaign.status = "paused"
                            session.add(campaign)
                            session.commit()
                            break

                        acc_email = account.email
                        acc_password = account.password
                        acc_phone = account.phone
                        acc_id = account.id
                        action_to_do = "order_checkout"

                    proxy = self.get_active_proxy(session)

                    camp_id = campaign.id
                    camp_keyword = campaign.keyword
                    camp_url = campaign.target_url
                    camp_seller = campaign.seller_name
                    camp_headless = campaign.headless
                    camp_payment = campaign.payment_method
                    camp_target_orders = campaign.target_orders_count
                    camp_delay_min = campaign.delay_min_sec or 10
                    camp_delay_max = campaign.delay_max_sec or 25
                    
                    proxy_url = proxy.proxy_url if proxy else None
                    proxy_rotation_url = proxy.rotation_url if proxy else None

                # 1. Zero-Touch Automated IP Rotation & Proxy Selection
                proxy_dict, rot_desc = await AutoProxyEngine.get_next_auto_proxy_and_rotate(
                    configured_proxy_url=proxy_url,
                    rotation_url=proxy_rotation_url
                )
                await self.log("info", f"[STEP 1/4] Network & IP Guard: {rot_desc}", acc_email)

                # 2. Execute with Playwright Stealth
                await self.log("info", f"[STEP 1/4] Launching Anti-Detect Stealth Session: {acc_email} (Mode: {c_type.upper()})", acc_email)
                context = None
                page = None
                try:
                    context, page = await browser_pool.create_account_context(
                        account_email=acc_email,
                        proxy_dict=proxy_dict,
                        headless=camp_headless
                    )
                    
                    async def bot_log(lvl, msg):
                        await self.log(lvl, msg, acc_email)
                        
                    bot = DarazBotEngine(page, context, log_callback=bot_log)
                    
                    # Login is only required for real order_checkout, not for ATC rank boosting
                    if acc_password and c_type == "order_checkout":
                        login_ok = await bot.check_and_login(acc_email, acc_password, acc_phone)
                        if not login_ok:
                            with Session(engine) as session:
                                db_acc = session.get(Account, acc_id)
                                if db_acc:
                                    db_acc.status = "needs_otp"
                                    session.add(db_acc)
                                    session.commit()
                            await self.log("warning", f"Account {acc_email} needs verification. Switching to next account.", acc_email)
                            continue

                    # 3. Organic Keyword Search & Dwell Simulation
                    await self.log("info", f"[STEP 2/4] Navigating to Daraz & Searching Keyword...", acc_email)
                    search_ok = await bot.organic_search_and_browse(
                        keyword=camp_keyword,
                        target_url=camp_url,
                        seller_name=camp_seller
                    )

                    # 4. Mode Actions: ATC / Wishlist or Checkout
                    if c_type == "atc_rank_boost":
                        await self.log("info", f"[STEP 3/4] Adding to Wishlist & Simulating Buyer Interest...", acc_email)
                        await bot.add_to_wishlist()
                        
                        await self.log("info", f"[STEP 4/4] Executing Add to Cart...", acc_email)
                        atc_success = await bot.add_to_cart()
                        
                        with Session(engine) as session:
                            c = session.get(Campaign, camp_id)
                            if c:
                                if atc_success:
                                    c.completed_atc_count += 1
                                c.completed_wishlist_count += 1
                                session.add(c)
                                session.commit()
                                await self.log("success", f"[COMPLETED] Add to Cart & Wishlist Success! Total Progress: {c.completed_atc_count}/{c.target_atc_count} ATCs | {c.completed_wishlist_count} Wishlists", acc_email)

                    elif action_to_do == "order_checkout":
                        await self.log("info", f"[STEP 3/4] Proceeding to Checkout & Address Autofill...", acc_email)
                        order_res = await bot.checkout_and_place_order(payment_method=camp_payment)
                        if order_res.get("success"):
                            with Session(engine) as session:
                                c = session.get(Campaign, camp_id)
                                if c:
                                    c.completed_orders_count += 1
                                    session.add(c)
                                
                                db_acc = session.get(Account, acc_id)
                                if db_acc:
                                    db_acc.daily_orders_count += 1
                                    db_acc.total_orders_placed += 1
                                    db_acc.last_used_at = datetime.datetime.utcnow()
                                    if db_acc.daily_orders_count >= db_acc.max_daily_orders:
                                        db_acc.status = "cooldown"
                                    session.add(db_acc)
                                session.commit()
                            max_quota = db_acc.max_daily_orders if db_acc else 5
                            await self.log("success", f"[COMPLETED] Order Placed Successfully! (Account: {acc_email} | Orders Today: {db_acc.daily_orders_count if db_acc else 1}/{max_quota})", acc_email)

                    # Update UI progress
                    if self.broadcast:
                        with Session(engine) as session:
                            c = session.get(Campaign, camp_id)
                            if c:
                                await self.broadcast({
                                    "type": "campaign_progress",
                                    "campaign": c.model_dump()
                                })

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    await self.log("error", f"Error during browser execution: {e}", acc_email)
                finally:
                    if context:
                        try:
                            await context.close()
                        except Exception:
                            pass

                # Check if stop was requested while executing
                if self.stop_requested:
                    break

                # Randomized human delay between consecutive executions
                delay_seconds = random.randint(camp_delay_min, camp_delay_max)
                await self.log("info", f"Waiting {delay_seconds} seconds before next task...", acc_email)
                try:
                    await asyncio.sleep(delay_seconds)
                except asyncio.CancelledError:
                    break


        finally:
            self.is_running = False
            with Session(engine) as session:
                c = self.get_campaign(session)
                if c and c.status == "running":
                    c.status = "paused" if self.stop_requested else "idle"
                    session.add(c)
                    session.commit()
                    
            if self.broadcast:
                try:
                    with Session(engine) as session:
                        c = self.get_campaign(session)
                        if c:
                            await self.broadcast({
                                "type": "campaign_progress",
                                "campaign": c.model_dump()
                            })
                except Exception:
                    pass

class TaskScheduler:
    def __init__(self):
        self.active_runners: Dict[int, CampaignRunner] = {}
        self.broadcast_callback: Optional[Callable] = None

    def set_broadcast(self, cb: Callable):
        self.broadcast_callback = cb

    def reset_stuck_campaigns(self):
        """Resets any campaigns that were left in running state upon server restart."""
        with Session(engine) as session:
            stuck = session.exec(select(Campaign).where(Campaign.status == "running")).all()
            for c in stuck:
                c.status = "idle"
                session.add(c)
            session.commit()

    async def start_campaign(self, campaign_id: int):
        # If already running, return status
        if campaign_id in self.active_runners and self.active_runners[campaign_id].is_running:
            return {"status": "already_running"}
            
        runner = CampaignRunner(campaign_id, self.broadcast_callback)
        self.active_runners[campaign_id] = runner
        runner.task = asyncio.create_task(runner.run())
        return {"status": "started", "campaign_id": campaign_id}

    async def stop_campaign(self, campaign_id: int):
        # 1. Cancel active runner if exists
        if campaign_id in self.active_runners:
            runner = self.active_runners[campaign_id]
            runner.stop_requested = True
            if runner.task and not runner.task.done():
                runner.task.cancel()
            del self.active_runners[campaign_id]
            
        # 2. Guarantee database status is paused/idle
        with Session(engine) as session:
            c = session.get(Campaign, campaign_id)
            if c:
                c.status = "paused"
                session.add(c)
                session.commit()
                
        # 3. Broadcast update to UI
        if self.broadcast_callback:
            try:
                with Session(engine) as session:
                    c = session.get(Campaign, campaign_id)
                    if c:
                        await self.broadcast_callback({
                            "type": "campaign_progress",
                            "campaign": c.model_dump()
                        })
            except Exception:
                pass
                
        return {"status": "stopped", "campaign_id": campaign_id}

    async def reset_all_campaigns(self):
        """Force resets all campaigns back to idle or paused."""
        for cid, runner in list(self.active_runners.items()):
            runner.stop_requested = True
            if runner.task and not runner.task.done():
                runner.task.cancel()
        self.active_runners.clear()
        
        with Session(engine) as session:
            camps = session.exec(select(Campaign)).all()
            for c in camps:
                if c.status == "running":
                    c.status = "idle"
                    session.add(c)
            session.commit()
        return {"status": "all_reset"}

scheduler = TaskScheduler()
