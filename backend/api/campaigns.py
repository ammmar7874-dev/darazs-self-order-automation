from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from sqlmodel import Session, select
from backend.database import engine, Campaign
from backend.core.task_scheduler import scheduler
import datetime

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"])

class CampaignCreate(BaseModel):
    name: str
    campaign_type: str = "atc_rank_boost" # "atc_rank_boost" (Solution 4) or "order_checkout" (1 Order/ID/Day)
    target_url: str
    keyword: str
    seller_name: Optional[str] = None
    target_orders_count: int = 1
    target_atc_count: int = 20
    target_wishlist_count: int = 10
    delay_min_sec: int = 10
    delay_max_sec: int = 30
    headless: bool = False
    payment_method: str = "cod"

class BatchCampaignCreate(BaseModel):
    batch_text: str # lines of: URL | Keyword | OrdersCount | ATCCount | SellerName
    campaign_type: str = "atc_rank_boost"
    default_orders: int = 1
    default_atc: int = 25
    default_wishlist: int = 10
    delay_min_sec: int = 10
    delay_max_sec: int = 30
    headless: bool = False

@router.get("", response_model=List[Campaign])
def list_campaigns():
    with Session(engine) as session:
        return session.exec(select(Campaign).order_by(Campaign.id.desc())).all()

@router.post("", response_model=Campaign)
def create_campaign(data: CampaignCreate):
    with Session(engine) as session:
        camp = Campaign(
            name=data.name.strip(),
            campaign_type=data.campaign_type,
            target_url=data.target_url.strip(),
            keyword=data.keyword.strip(),
            seller_name=data.seller_name.strip() if data.seller_name else None,
            target_orders_count=data.target_orders_count,
            target_atc_count=data.target_atc_count,
            target_wishlist_count=data.target_wishlist_count,
            delay_min_sec=data.delay_min_sec,
            delay_max_sec=data.delay_max_sec,
            headless=data.headless,
            payment_method=data.payment_method,
            status="idle"
        )
        session.add(camp)
        session.commit()
        session.refresh(camp)
        return camp

@router.post("/batch")
def create_batch_campaigns(data: BatchCampaignCreate):
    """
    Creates multiple product ranking/order campaigns in bulk.
    Format per line: URL | Keyword | (optional: Orders) | (optional: ATC) | (optional: Seller)
    Or simply raw URLs (keyword extracted from product URL title slug).
    """
    lines = data.batch_text.strip().split("\n")
    created_count = 0
    with Session(engine) as session:
        for idx, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split("|")]
            url = parts[0]
            
            # Default keyword derived from URL if not given
            keyword = parts[1] if len(parts) > 1 and parts[1] else "Daraz Top Product"
            if len(parts) == 1 and "/products/" in url:
                # Extract slug
                slug = url.split("/products/")[1].split("-i")[0].replace("-", " ")
                keyword = slug.title()
                
            orders_cnt = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else data.default_orders
            atc_cnt = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else data.default_atc
            seller = parts[4] if len(parts) > 4 else None

            camp = Campaign(
                name=f"Batch #{idx} - {keyword[:30]}",
                target_url=url,
                keyword=keyword,
                seller_name=seller,
                target_orders_count=orders_cnt,
                target_atc_count=atc_cnt,
                target_wishlist_count=data.default_wishlist,
                delay_min_sec=data.delay_min_sec,
                delay_max_sec=data.delay_max_sec,
                headless=data.headless,
                status="idle"
            )
            session.add(camp)
            created_count += 1
            
        session.commit()
    return {"status": "success", "created_campaigns": created_count}

@router.post("/{campaign_id}/start")
async def start_campaign(campaign_id: int):
    res = await scheduler.start_campaign(campaign_id)
    return res

@router.post("/{campaign_id}/stop")
async def stop_campaign(campaign_id: int):
    res = await scheduler.stop_campaign(campaign_id)
    return res

@router.post("/reset-all")
async def reset_all_campaigns():
    res = await scheduler.reset_all_campaigns()
    return res


@router.get("/export-csv")
def export_campaigns_csv():
    """Exports all campaigns with progress & results to CSV."""
    import io, csv
    from fastapi.responses import Response
    with Session(engine) as session:
        campaigns = session.exec(select(Campaign).order_by(Campaign.id.asc())).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Name", "Type", "Keyword", "Target URL", "Orders Done", "Orders Target", "ATC Done", "ATC Target", "Wishlists Done", "Status", "Created At"])
        for c in campaigns:
            writer.writerow([
                c.id, c.name, c.campaign_type or "atc_rank_boost", c.keyword, c.target_url,
                c.completed_orders_count, c.target_orders_count,
                c.completed_atc_count, c.target_atc_count,
                c.completed_wishlist_count, c.status,
                c.created_at.strftime("%Y-%m-%d %H:%M:%S") if c.created_at else ""
            ])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=daraz_campaigns_export.csv"}
        )

@router.delete("/{campaign_id}")
def delete_campaign(campaign_id: int):
    with Session(engine) as session:
        c = session.get(Campaign, campaign_id)
        if not c:
            raise HTTPException(status_code=404, detail="Campaign not found")
        session.delete(c)
        session.commit()
        return {"status": "deleted", "campaign_id": campaign_id}

class StoreScrapeRequest(BaseModel):
    store_url: str

class StoreProductItem(BaseModel):
    id: Optional[str] = None
    url: str
    title: str
    img: Optional[str] = None
    keywords: Optional[List[str]] = None

class BulkStoreBoostRequest(BaseModel):
    store_url: str
    products: List[StoreProductItem]
    target_atc: int = 10
    target_wishlist: int = 10
    follow_store: bool = True
    collect_vouchers: bool = True
    upvote_reviews: bool = True
    headless: bool = False

@router.post("/scrape-store")
async def scrape_store_products(data: StoreScrapeRequest):
    """Scrapes all product listings from any Daraz Store URL."""
    from backend.core.browser_pool import browser_pool
    from backend.core.daraz_bot import DarazBotEngine
    
    clean_url = data.store_url.strip()
    if not clean_url.startswith("http"):
        clean_url = f"https://www.daraz.pk/shop/{clean_url}"
        
    context, page = await browser_pool.create_account_context(
        account_email="guest_scraper",
        headless=True
    )
    try:
        bot = DarazBotEngine(page, context)
        products = await bot.scrape_store_catalog(clean_url)
        return {
            "status": "success",
            "store_url": clean_url,
            "total_products": len(products),
            "products": products
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scrape store: {str(e)}")
    finally:
        try:
            await context.close()
        except Exception:
            pass

@router.post("/bulk-store-boost")
async def bulk_store_boost(data: BulkStoreBoostRequest):
    """Queues campaigns for all selected store products in database."""
    created = []
    with Session(engine) as session:
        for p in data.products:
            # Check if campaign already exists
            camp = session.exec(select(Campaign).where(Campaign.target_url == p.url)).first()
            if not camp:
                kw_str = ", ".join(p.keywords) if p.keywords else p.title[:40]
                camp = Campaign(
                    name=f"Store Boost - {p.title[:35]}",
                    target_url=p.url,
                    keyword=kw_str,
                    target_atc_count=data.target_atc,
                    target_wishlist_count=data.target_wishlist,
                    target_orders_count=1,
                    delay_min_sec=10,
                    delay_max_sec=30,
                    headless=data.headless,
                    status="idle"
                )
                session.add(camp)
                session.commit()
                session.refresh(camp)
            created.append(camp.id)

    return {
        "status": "success",
        "message": f"Successfully queued {len(created)} store product campaigns!",
        "campaign_ids": created
    }

class RankCheckRequest(BaseModel):
    keyword: str
    target_url: str
    max_pages: int = 5

@router.post("/rank-checker/check")
async def check_product_serp_rank(data: RankCheckRequest):
    """
    Scans Daraz search engine in real-time to find the exact SERP page, slot position,
    and organic vs sponsored rank of any product.
    """
    from backend.core.browser_pool import browser_pool
    from backend.core.daraz_bot import DarazBotEngine
    from backend.database import RankCheckHistory

    kw = data.keyword.strip()
    target_url = data.target_url.strip()
    if not kw or not target_url:
        raise HTTPException(status_code=400, detail="Keyword and Target URL/ID are required.")

    context, page = await browser_pool.create_account_context(
        account_email="rank_checker_bot",
        headless=True
    )
    try:
        bot = DarazBotEngine(page, context)
        result = await bot.check_keyword_serp_rank(
            keyword=kw,
            target_id_or_url=target_url,
            max_pages=data.max_pages
        )

        # Store in database history
        with Session(engine) as session:
            entry = RankCheckHistory(
                product_id=result.get("target_id") or target_url,
                product_title=result.get("product_title"),
                product_url=result.get("product_url") or target_url,
                keyword=kw,
                page_number=result.get("page") or 0,
                rank_position=result.get("overall_rank") or 0,
                is_sponsored=result.get("is_sponsored", False),
                total_results_found=result.get("total_scanned", 0)
            )
            session.add(entry)
            session.commit()

        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rank check error: {str(e)}")
    finally:
        try:
            await context.close()
        except Exception:
            pass

@router.get("/rank-checker/history")
def get_rank_check_history(limit: int = 30):
    from backend.database import RankCheckHistory
    with Session(engine) as session:
        return session.exec(select(RankCheckHistory).order_by(RankCheckHistory.id.desc())).all()[:limit]


