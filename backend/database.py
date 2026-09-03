import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, create_engine, Session, select, text
from backend.config import settings

class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password: str
    phone: Optional[str] = None
    full_name: Optional[str] = "Customer"
    shipping_address: Optional[str] = None
    city: Optional[str] = "Karachi"
    status: str = Field(default="active") # active, cooldown, banned, needs_otp
    session_status: str = Field(default="unknown") # valid, expired, needs_login, unknown
    cookies_json: Optional[str] = None # Serialized Playwright browser session cookies
    daily_orders_count: int = Field(default=0)
    total_orders_placed: int = Field(default=0)
    max_daily_orders: int = Field(default=5) # 4-5 Orders per ID per Day (Distributed via Round-Robin Rotation)
    last_used_at: Optional[datetime.datetime] = None
    cooldown_until: Optional[datetime.datetime] = None
    notes: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class Proxy(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    proxy_url: str # format: http://user:pass@host:port or host:port
    proxy_type: str = Field(default="residential") # residential, mobile_dongle, datacenter, free_global
    rotation_url: Optional[str] = None # API endpoint to trigger dynamic IP change (e.g. mobile 4g IP refresh)
    is_active: bool = Field(default=True)
    last_ip: Optional[str] = None
    last_tested_at: Optional[datetime.datetime] = None
    success_count: int = Field(default=0)
    fail_count: int = Field(default=0)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class Campaign(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    campaign_type: str = Field(default="atc_rank_boost") # "atc_rank_boost" (Solution 4 - Infinite Ranking) or "order_checkout" (1 Order/ID/Day)
    target_url: str # Product URL or Store URL
    keyword: str # Organic search keyword e.g. "wireless earbuds bluetooth 5.3"
    seller_name: Optional[str] = None # Target seller store name for verification
    target_orders_count: int = Field(default=1)
    completed_orders_count: int = Field(default=0)
    target_atc_count: int = Field(default=20) # Add to cart target
    completed_atc_count: int = Field(default=0)
    target_wishlist_count: int = Field(default=10)
    completed_wishlist_count: int = Field(default=0)
    status: str = Field(default="idle") # idle, running, paused, completed, failed
    delay_min_sec: int = Field(default=10)
    delay_max_sec: int = Field(default=30)
    headless: bool = Field(default=False)
    payment_method: str = Field(default="cod") # Cash on Delivery
    notes: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class TaskItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(index=True)
    account_id: Optional[int] = None
    account_email: Optional[str] = None
    proxy_id: Optional[int] = None
    action_type: str = Field(default="order_checkout") # search_browse, add_to_cart, order_checkout
    status: str = Field(default="pending") # pending, running, success, failed
    error_message: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    started_at: Optional[datetime.datetime] = None
    finished_at: Optional[datetime.datetime] = None

class ExecutionLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: Optional[int] = Field(default=None, index=True)
    account_email: Optional[str] = None
    level: str = Field(default="info") # info, success, warning, error
    message: str
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class RankCheckHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: str = Field(index=True)
    product_title: Optional[str] = None
    product_url: str
    keyword: str = Field(index=True)
    page_number: int = Field(default=1)
    rank_position: int = Field(default=0) # 0 means not in top pages scanned
    is_sponsored: bool = Field(default=False)
    total_results_found: int = Field(default=0)
    checked_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

engine = create_engine(settings.db_url, echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)
    # Safe auto-migration for existing SQLite databases
    with engine.connect() as conn:
        for query in [
            "ALTER TABLE campaign ADD COLUMN campaign_type VARCHAR DEFAULT 'atc_rank_boost'",
            "ALTER TABLE account ADD COLUMN session_status VARCHAR DEFAULT 'unknown'",
            "ALTER TABLE account ADD COLUMN cookies_json TEXT",
        ]:
            try:
                conn.execute(text(query))
                conn.commit()
            except Exception:
                pass # Column already exists

def get_session():
    with Session(engine) as session:
        yield session
