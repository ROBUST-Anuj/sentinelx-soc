from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings
import os

def normalize_async_db_url(url: str) -> str:
    """
    Ensure PostgreSQL URLs use the asyncpg driver when creating async engines.
    Handles standard provider formats:
    - postgres:// -> postgresql+asyncpg://
    - postgresql:// -> postgresql+asyncpg://
    - sqlite:// -> sqlite+aiosqlite://
    """
    if not url:
        return "sqlite+aiosqlite:///./data/sentinelx.db"
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite://") and not url.startswith("sqlite+"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url

def normalize_sync_db_url(url: str) -> str:
    """
    Ensure synchronous URLs are compatible with standard drivers (psycopg2/sqlite).
    """
    if not url:
        return "sqlite:///./data/sentinelx.db"
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if url.startswith("sqlite+aiosqlite://"):
        return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    return url

async_db_url = normalize_async_db_url(settings.DATABASE_URL)
sync_db_url = normalize_sync_db_url(settings.SYNC_DATABASE_URL)

# Configure connection pooling appropriate for cloud PostgreSQL vs local SQLite
engine_kwargs = {
    "echo": False,
    "future": True,
}

if "postgresql" in async_db_url:
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 5,
        "max_overflow": 10
    })

# Asynchronous engine and sessionmaker
async_engine = create_async_engine(
    async_db_url,
    **engine_kwargs
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

sync_engine_kwargs = {"echo": False, "future": True}
if "postgresql" in sync_db_url:
    sync_engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_recycle": 300
    })

# Synchronous engine for migrations, initial seeding, and background scripts
sync_engine = create_engine(
    sync_db_url,
    **sync_engine_kwargs
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
