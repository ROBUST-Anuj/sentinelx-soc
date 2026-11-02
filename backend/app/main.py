from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import async_engine, Base, AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.db_models import User, BankAccount
from app.api.endpoints import api_router
from app.banking.routes import banking_router
from app.banking.internal_routes import internal_router
from app.banking.telemetry_routes import telemetry_router
from app.banking.storyline_routes import storyline_router
from app.banking.orchestration_routes import orchestration_router
from app.banking.enforcement_routes import enforcement_router
from app.banking.intel_routes import intel_router
from app.banking.command_center_routes import command_center_router
from sqlalchemy.future import select
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentinelx")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create DB tables and default seed admin
    logger.info("Initializing SentinelX Database Schema...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Versioned, non-destructive schema migration tracking:
        from sqlalchemy import text
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(64) PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description VARCHAR(255)
                );
            """))
            applied_res = await conn.execute(text("SELECT version FROM schema_migrations;"))
            applied_versions = {row[0] for row in applied_res.fetchall()}
        except Exception as e:
            logger.debug(f"schema_migrations table init notice: {e}")
            applied_versions = set()

        migration_registry = [
            ("20260401_threat_intel_first_seen", "ALTER TABLE threat_indicators ADD COLUMN IF NOT EXISTS first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"),
            ("20260401_threat_intel_last_seen", "ALTER TABLE threat_indicators ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"),
            ("20260401_threat_intel_expires_at", "ALTER TABLE threat_indicators ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP;"),
            ("20260401_threat_intel_metadata", "ALTER TABLE threat_indicators ADD COLUMN IF NOT EXISTS metadata_info JSON DEFAULT '{}';"),
            ("20260402_audit_prev_hash", "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS prev_hash VARCHAR;"),
            ("20260402_audit_entry_hash", "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS entry_hash VARCHAR DEFAULT 'GENESIS';"),
            ("20260402_audit_resource_type", "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS resource_type VARCHAR DEFAULT 'system';"),
            ("20260402_audit_resource_id", "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS resource_id VARCHAR;"),
            ("20260403_incidents_entities", "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS affected_entities JSON DEFAULT '[]';"),
            ("20260403_incidents_intel_matches", "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS threat_intel_matches JSON DEFAULT '[]';"),
            ("20260403_incidents_graph_score", "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS graph_risk_score FLOAT DEFAULT 0.0;")
        ]

        for version, stmt in migration_registry:
            if version not in applied_versions:
                try:
                    await conn.execute(text(stmt))
                    try:
                        await conn.execute(text("INSERT INTO schema_migrations (version, description) VALUES (:v, :d)"), {"v": version, "d": stmt[:250]})
                    except Exception:
                        pass
                except Exception as e:
                    logger.debug(f"Schema migration statement notice ({version}): {e}")
        
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

        # Seed synthetic bank accounts for demo users if none exist
        admin_acc_stmt = select(BankAccount).where(BankAccount.account_number == "ACT-SYNTH-1001")
        admin_acc_res = await session.execute(admin_acc_stmt)
        if not admin_acc_res.scalars().first():
            # Get admin and analyst users
            admin_user = (await session.execute(select(User).where(User.username == "admin"))).scalars().first()
            analyst_user = (await session.execute(select(User).where(User.username == "analyst"))).scalars().first()
            if admin_user:
                acc_admin = BankAccount(
                    user_id=admin_user.id,
                    account_number="ACT-SYNTH-1001",
                    account_type="checking",
                    currency="INR",
                    balance_minor=1_000_000_00,  # ₹10,00,000.00
                    status="active",
                    is_synthetic=True
                )
                session.add(acc_admin)
            if analyst_user:
                acc_analyst = BankAccount(
                    user_id=analyst_user.id,
                    account_number="ACT-SYNTH-2002",
                    account_type="savings",
                    currency="INR",
                    balance_minor=250_000_00,  # ₹2,50,000.00
                    status="active",
                    is_synthetic=True
                )
                session.add(acc_analyst)
                # Add a suspicious / restricted beneficiary account for security scenario testing
                acc_suspicious = BankAccount(
                    user_id=analyst_user.id,
                    account_number="ACT-SYNTH-9999",
                    account_type="merchant",
                    currency="INR",
                    balance_minor=50_000_00,
                    status="suspended",  # administrative lock
                    is_synthetic=True
                )
                session.add(acc_suspicious)
            await session.commit()
            logger.info("Seeded initial synthetic bank accounts (ACT-SYNTH-1001, ACT-SYNTH-2002, ACT-SYNTH-9999).")

        # Ensure restricted account ACT-SYNTH-9999 exists for fraud simulation scenarios
        susp_stmt = select(BankAccount).where(BankAccount.account_number == "ACT-SYNTH-9999")
        susp_res = await session.execute(susp_stmt)
        if not susp_res.scalars().first():
            admin_u = (await session.execute(select(User).where(User.username == "admin"))).scalars().first()
            if admin_u:
                acc_suspicious = BankAccount(
                    user_id=admin_u.id,
                    account_number="ACT-SYNTH-9999",
                    account_type="merchant",
                    currency="INR",
                    balance_minor=50_000_00,
                    status="suspended",
                    is_synthetic=True
                )
                session.add(acc_suspicious)
                await session.commit()
                logger.info("Seeded restricted beneficiary account ACT-SYNTH-9999.")
    yield
    # Shutdown
    logger.info("Shutting down SentinelX application services...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS configuration - strictly explicit environment-driven allowlist
raw_origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
MANDATORY_ORIGINS = [
    "https://frontend-sigma-liart-89.vercel.app",
    "https://nexabank-portal.vercel.app",
    "https://nexabank-frontend.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]
cors_origins = list(dict.fromkeys(raw_origins + MANDATORY_ORIGINS))
allow_creds = ("*" not in cors_origins)

cors_kwargs = {
    "allow_origins": cors_origins,
    "allow_credentials": allow_creds,
    "allow_methods": ["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["*"],
}
if settings.CORS_ORIGIN_REGEX:
    cors_kwargs["allow_origin_regex"] = settings.CORS_ORIGIN_REGEX

app.add_middleware(
    CORSMiddleware,
    **cors_kwargs
)

# Include Routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(banking_router, prefix=settings.API_V1_STR)
app.include_router(telemetry_router, prefix=settings.API_V1_STR)
app.include_router(storyline_router, prefix=settings.API_V1_STR)
app.include_router(orchestration_router, prefix=settings.API_V1_STR)
app.include_router(intel_router, prefix=settings.API_V1_STR)
app.include_router(command_center_router, prefix=settings.API_V1_STR)
app.include_router(enforcement_router)
app.include_router(internal_router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SentinelX SOC Core API",
        "version": settings.VERSION
    }
