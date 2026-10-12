# SentinelX SOC — Public Cloud Deployment Guide ($0, No Credit Card)

**Project:** SentinelX SOC  
**Application Architecture:** Full-Stack Cybersecurity SIEM & SOAR Platform  
**Target Cost:** $0.00 / month (Permanently Free Tier)  
**Payment Card Requirement:** Strictly None

---

## 1. Cloud Architecture Overview

```
                      ┌──────────────────────────────────────┐
                      │             PUBLIC USER              │
                      └──────────────────┬───────────────────┘
                                         │ HTTPS (TLS 1.3)
                                         ▼
                      ┌──────────────────────────────────────┐
                      │          VERCEL (FRONTEND)           │
                      │   https://sentinelx-soc.vercel.app   │
                      │       Vite React + Tailwind CSS      │
                      └──────────────────┬───────────────────┘
                                         │ API REST Requests (HTTPS)
                                         ▼
                      ┌──────────────────────────────────────┐
                      │           RENDER / HF SPACES         │
                      │     https://sentinelx-api.onrender   │
                      │        FastAPI + Uvicorn + ML        │
                      └──────────────────┬───────────────────┘
                                         │ AsyncPG Pool (SSL)
                                         ▼
                      ┌──────────────────────────────────────┐
                      │          SUPABASE POSTGRESQL         │
                      │       Cloud Persistent Database      │
                      │          500 MB Free Storage         │
                      └──────────────────────────────────────┘
```

---

## 2. Phase 1: Push Code to GitHub

### Prerequisites:
Make sure you have a free [GitHub account](https://github.com) (no credit card required).

### Commands to Run:
```powershell
# 1. Check Git status
git status

# 2. Stage verified application code and configuration
git add .gitignore .env.example Dockerfile.backend Dockerfile.frontend docker-compose.yml
git add backend/ frontend/ scripts/
git add *.md

# 3. Create a clean commit
git commit -m "feat(deploy): prepare hardened SentinelX SOC for zero-cost public cloud deployment"

# 4. Link to your personal GitHub repository (replace with your repo URL):
# git remote add origin https://github.com/YOUR_USERNAME/sentinelx-soc.git
# git branch -M main
# git push -u origin main
```

---

## 3. Phase 2: Provision Cloud PostgreSQL on Supabase ($0, No Card)

1. Navigate to **[supabase.com](https://supabase.com)** and sign in with GitHub.
2. Click **New Project** and name it `sentinelx-soc-db`.
3. Choose a strong database password (e.g. `SentinelX_DB_2026!`).
4. Select region: Choose the region closest to you (e.g. `East US` or `Central EU`).
5. Ensure pricing tier is **Free ($0/month)**. Click **Create new project**.
6. Once provisioned (~2 mins), go to **Project Settings** &rarr; **Database**.
7. Under **Connection string**, select **URI** and copy the string:
   ```
   postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres
   ```
   *(Keep this string ready for the backend configuration).*

---

## 4. Phase 3: Deploy FastAPI Backend on Render ($0, No Card)

Render's free tier provides 512 MB RAM and 0.1 CPU for web services without entering credit card details.

1. Navigate to **[render.com](https://render.com)** and click **Get Started for Free** (Sign in with GitHub).
2. Click **New +** &rarr; **Web Service**.
3. Select **Build and deploy from a Git repository** and connect your `sentinelx-soc` repository.
4. Configure the Web Service settings:
   - **Name**: `sentinelx-backend`
   - **Region**: Same region selected in Supabase (e.g. `Oregon (US West)` or `Frankfurt (EU)`).
   - **Branch**: `main` (or `master`)
   - **Root Directory**: `.` (leave empty or set to root)
   - **Runtime**: **Python 3** (or choose **Docker** and set Dockerfile path to `Dockerfile.backend`)
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend`
   - **Instance Type**: Select **Free ($0/month)**.

5. Click **Advanced** and add the following **Environment Variables**:
   | Key | Value | Notes |
   | :--- | :--- | :--- |
   | `ENVIRONMENT` | `production` | Enforces production security and dry-run locks |
   | `SECRET_KEY` | *(Generate a 32+ char random string)* | JWT signing key |
   | `DATABASE_URL` | `postgresql+asyncpg://postgres:PW@HOST:5432/postgres?ssl=require` | Supabase URI from Step 3 |
   | `SYNC_DATABASE_URL` | `postgresql://postgres:PW@HOST:5432/postgres?sslmode=require` | Supabase URI from Step 3 |
   | `CORS_ORIGINS` | `https://YOUR_APP.vercel.app,http://localhost:3000` | Will be updated with your Vercel URL |
   | `ADMIN_PASSWORD` | `Admin@SentinelX2026` | Initial master password for admin |

6. Click **Create Web Service**.
7. Render will build and deploy the service. Once finished, copy your assigned public HTTPS URL:
   `https://sentinelx-backend.onrender.com`
8. Verify health in your browser or terminal:
   ```powershell
   curl.exe -s https://sentinelx-backend.onrender.com/health
   # Expected: {"status":"healthy","service":"SentinelX SOC Core API","version":"1.0.0"}
   ```

---

## 5. Phase 4: Deploy Vite React Frontend on Vercel ($0, No Card)

Vercel provides free, high-performance global CDN hosting for Vite applications without entering credit card details.

1. Navigate to **[vercel.com](https://vercel.com)** and sign in with GitHub.
2. Click **Add New...** &rarr; **Project**.
3. Import your `sentinelx-soc` repository.
4. In the Project Configuration screen:
   - **Framework Preset**: Select **Vite** (detected automatically).
   - **Root Directory**: Click *Edit* and select **`frontend`**.
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Expand **Environment Variables** and add:
   | Key | Value |
   | :--- | :--- |
   | `VITE_API_BASE_URL` | `https://sentinelx-backend.onrender.com/api` (use your actual Render backend URL) |
   | `VITE_DEMO_PRESETS` | `true` (enables one-click demo logins for examination viva) |
6. Click **Deploy**.
7. Within ~45 seconds, Vercel will complete the build and assign your production HTTPS URL:
   `https://sentinelx-soc.vercel.app`

---

## 6. Phase 5: Post-Deployment Sync & Acceptance Check

1. In Render Dashboard, update `CORS_ORIGINS` to include your new Vercel domain:
   ```
   https://sentinelx-soc.vercel.app,http://localhost:3000
   ```
2. Open `https://sentinelx-soc.vercel.app` in your browser.
3. Sign in using the admin account (`admin` / `Admin@SentinelX2026`).
4. Execute the live acceptance runbook ([`LIVE_DEMO_RUNBOOK.md`](file:///c:/Users/aditya%20parashar/OneDrive/Desktop/Cyber/LIVE_DEMO_RUNBOOK.md)).
