# SentinelX SOC & Banking Gateway — Deployment Runbook

## 1. Hosting Architecture Overview

| Tier | Platform | Technology | URL / Port |
|---|---|---|---|
| **Production Backend** | Render | Python 3.11+, FastAPI, Uvicorn | `https://sentinelx-api-316t.onrender.com` (Port 8000) |
| **Production Frontend** | Vercel | React 19, TypeScript, Vite | `https://frontend-sigma-liart-89.vercel.app/` |
| **Static Demo Showcase** | Hugging Face Spaces | Static HTML / JS (No paid compute) | `https://anuj1555-sentinelx-soc-demo.static.hf.space` |
| **Local / Air-Gapped** | Docker Compose | Docker, PostgreSQL / SQLite | Ports 3000 (UI), 8888 (API) |

---

## 2. Environment Variables Checklist

### Backend (`backend/.env` or Render Dashboard)
| Variable | Value / Format | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/db` or `sqlite+aiosqlite:///./sentinelx.db` | Async SQLAlchemy database connection string |
| `JWT_SECRET` | Strong cryptographic random hex string | JWT token signing key |
| `PORT` | `8000` | Port for Uvicorn web server binding |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins (e.g. Vercel, HF Space, localhost) | Cross-Origin Resource Sharing allowlist |

### Frontend (`frontend/.env` or Vercel Dashboard)
| Variable | Value | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `https://sentinelx-api-316t.onrender.com` | Base URL pointing React client to FastAPI backend |

---

## 3. Local Deployment via Docker Compose

To spin up the complete integrated stack locally:

```bash
# 1. Build and start services in detached mode
docker-compose up -d --build

# 2. Check service status
docker-compose ps

# 3. Access frontend command deck
http://localhost:3000

# 4. Access interactive OpenAPI documentation
http://localhost:8888/docs
```

---

## 4. Verification & Healthchecks

### Backend Health Check
```bash
curl -f https://sentinelx-api-316t.onrender.com/health
# Expected Response: {"status":"healthy","database":"connected","version":"2.0.0"}
```

### Banking API Health Check
```bash
curl -f https://sentinelx-api-316t.onrender.com/api/banking/accounts
```

### Static Hugging Face Space Synchronization
To sync the static demo files to the Hugging Face Space repository:
```bash
# Build frontend
cd frontend && npm run build && cd ..

# Copy dist assets to static space deployment folder
cp -r frontend/dist/* deploy/hf-static-space/
```
