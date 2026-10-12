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
            initial_admin_pw = os.getenv("ADMIN_PASSWORD", "Admin@SentinelX2026")
            new_admin = User(
                username="admin",
                email="admin@sentinelx.local",
                hashed_password=get_password_hash(initial_admin_pw),
                role="admin",
                is_active=True
            )
            session.add(new_admin)
            
            # Also seed demo analyst
            initial_analyst_pw = os.getenv("ANALYST_PASSWORD", "Analyst@SentinelX2026")
            analyst = User(
                username="analyst",
                email="analyst@sentinelx.local",
                hashed_password=get_password_hash(initial_analyst_pw),
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

# CORS configuration
cors_origins = settings.CORS_ORIGINS if settings.ENVIRONMENT == "production" else ["*"]
allow_creds = True if settings.ENVIRONMENT != "production" or "*" not in cors_origins else False

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_creds,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
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
