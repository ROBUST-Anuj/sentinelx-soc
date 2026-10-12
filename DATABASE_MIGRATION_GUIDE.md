# SentinelX SOC — PostgreSQL Database Migration & Integration Guide

**Platform:** SentinelX SOC  
**Target Environments:** Cloud Managed PostgreSQL (Supabase / Neon.tech) and Local Development (SQLite)

---

## 1. Overview & Dual-Engine Architecture

SentinelX SOC uses **SQLAlchemy 2.0** with native asynchronous engine support. To support cloud hosting with persistent storage without requiring payment cards, the database layer in [`backend/app/core/database.py`](file:///c:/Users/aditya%20parashar/OneDrive/Desktop/Cyber/backend/app/core/database.py) dynamically normalizes connection strings:

| Target Provider | Raw Input Format | Normalized Async Driver | Normalized Sync Driver |
| :--- | :--- | :--- | :--- |
| **Local SQLite** | `sqlite:///./data/sentinelx.db` | `sqlite+aiosqlite:///./data/sentinelx.db` | `sqlite:///./data/sentinelx.db` |
| **Supabase Cloud** | `postgresql://postgres:[pw]@[host]:5432/postgres` | `postgresql+asyncpg://postgres:[pw]@[host]:5432/postgres` | `postgresql://postgres:[pw]@[host]:5432/postgres` |
| **Neon.tech** | `postgres://[user]:[pw]@[host]/neondb` | `postgresql+asyncpg://[user]:[pw]@[host]/neondb` | `postgresql://[user]:[pw]@[host]/neondb` |

---

## 2. Step-by-Step Provisioning on Supabase ($0, No Card)

1. **Sign Up on Supabase:**
   - Go to [supabase.com](https://supabase.com) and click **Start your project**.
   - Authenticate with your **GitHub account**.
   - **No credit card or billing information is required.**

2. **Create New Project:**
   - Click **New project**.
   - Choose a project name: `sentinelx-soc-db`.
   - Set a strong database password (e.g., generate a 24-character random string).
   - Select the closest cloud region (e.g., `us-east-1` or `eu-central-1`).
   - Pricing plan remains on the default **Free Plan** ($0/month, 500 MB storage).
   - Click **Create new project** and wait ~90 seconds for provisioning.

3. **Obtain Connection String:**
   - In project settings, navigate to **Project Settings** &rarr; **Database**.
   - Scroll to **Connection string** and select **URI** (or **Transaction Pooler**).
   - Copy the URI, which looks like:
     ```
     postgresql://postgres.[ref]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
     ```
   - Replace `[YOUR-PASSWORD]` with your chosen database password.

---

## 3. Applying Database Schema Migrations

SentinelX SOC automates table creation and default administrator seeding on application boot via its FastAPI lifespan handler:

```python
async with async_engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

To run a standalone verification script against your cloud database before deploying the web backend:

```powershell
# Set cloud database connection in terminal session
$env:DATABASE_URL="postgresql+asyncpg://postgres:[PW]@[HOST]:5432/postgres?ssl=require"
$env:SYNC_DATABASE_URL="postgresql://postgres:[PW]@[HOST]:5432/postgres?sslmode=require"

# Execute schema setup test
python -c "
import asyncio
from app.core.database import async_engine, Base
async def init():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('PostgreSQL schema successfully created!')
asyncio.run(init())
"
```

---

## 4. Connection Pooling & Reconnect Resilience

Cloud serverless PostgreSQL instances enforce strict connection limits on free tiers (typically 20–60 concurrent connections). The SentinelX database engine configures:
- `pool_pre_ping=True`: Probes connections before issuing SQL to prevent `SSL connection has been closed unexpectedly` errors after idle periods.
- `pool_recycle=300`: Refreshes connections every 5 minutes to gracefully handle cloud proxy timeouts.
- `pool_size=5` and `max_overflow=10`: Bounds peak connection usage within free tier limits.
