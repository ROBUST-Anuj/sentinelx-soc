from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import async_engine, Base, AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.db_models import User
from app.api.endpoints import api_router
from sqlalchemy.future import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentinelx")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create DB tables and default seed admin
    logger.info("Initializing SentinelX Database Schema...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as session:
        # Check if default admin exists
        res = await session.execute(select(User).where(User.username == "admin"))
        admin = res.scalars().first()
        if not admin:
            logger.info("Seeding default Administrator account (admin)...")
            new_admin = User(
                username="admin",
                email="admin@sentinelx.local",
                hashed_password=get_password_hash("Admin@SentinelX2026"),
                role="admin",
                is_active=True
            )
            session.add(new_admin)
            
            # Also seed demo analyst
            analyst = User(
                username="analyst",
                email="analyst@sentinelx.local",
                hashed_password=get_password_hash("Analyst@SentinelX2026"),
                role="analyst",
                is_active=True
            )
            session.add(analyst)
            await session.commit()
    yield
    # Shutdown
    logger.info("Shutting down SentinelX application services...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SentinelX SOC Core API",
        "version": settings.VERSION
    }
