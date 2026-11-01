# SentinelX SOC & NexaBank Banking Platform — Deployment Runbook

## 1. Multi-Tier Hosting Architecture

The platform is designed as an enterprise two-application ecosystem:

| Tier | Component | Platform | Technology Stack | Production / Local Target |
|---|---|---|---|---|
| **SOC Portal** | SentinelX SOC Command Center | Vercel | React 19, TypeScript, Vite, Tailwind | `https://frontend-sigma-liart-89.vercel.app/` (Local: `http://localhost:5173`) |
| **Banking Portal** | NexaBank Digital Banking Platform | Vercel | React 19, TypeScript, Vite, Lucide | Deployed Vercel URL (Local: `http://localhost:5174`) |
| **Central Backend** | SentinelX SOC & Banking Core API | Render | Python 3.11+, FastAPI, SQLAlchemy, NetworkX | `https://sentinelx-api-316t.onrender.com` (Local: `http://localhost:8000`) |
| **Database** | Persistent Relational Store | Neon / Supabase / SQLite | PostgreSQL 15+ (Prod) / SQLite (Dev) | Async SQLAlchemy via `asyncpg` / `aiosqlite` |
| **Static Showcase** | Live Demonstration Space | Hugging Face Spaces | Static HTML/JS | `https://anuj1555-sentinelx-soc-demo.static.hf.space` |

---

## 2. Environment Variables Checklist

### 2.1 Backend (`backend/.env` or Render Dashboard)
| Variable | Value / Format | Purpose | Required in Prod |
|---|---|---|:---:|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/dbname` | Async PostgreSQL database connection string | Yes |
| `JWT_SECRET` | 64-character hexadecimal cryptographically secure random string | Secret key for signing and validating analyst/customer JWTs | Yes |
| `INTERNAL_SERVICE_KEY` | Hexadecimal secret string | Shared secret for HMAC-authenticated inter-service API calls (`X-Service-Auth`) | Yes |
| `PORT` | `8000` | Port for Uvicorn ASGI server binding | Yes |
| `CORS_ORIGINS` | `https://frontend-sigma-liart-89.vercel.app,http://localhost:5173,http://localhost:5174` | Comma-delimited list of allowed origin URLs | Yes |
| `ENVIRONMENT` | `production` or `development` | Runtime environment mode | No (Defaults to `production`) |

### 2.2 SentinelX SOC Frontend (`frontend/.env` or Vercel Dashboard)
| Variable | Value | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `https://sentinelx-api-316t.onrender.com` | Base URL pointing the SOC React client to the FastAPI backend |

### 2.3 NexaBank Digital Banking Frontend (`banking-platform/frontend/.env` or Vercel Dashboard)
| Variable | Value | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `https://sentinelx-api-316t.onrender.com` | Base URL pointing the banking React client to the banking endpoints |
| `VITE_PORT` | `5174` | Local development port to avoid collision with SentinelX SOC (5173) |

---

## 3. Local Development Deployment

### Option A: Native Development (Side-by-Side Dual Port)

#### 1. Backend Service (Port 8000)
```powershell
# Navigate to project root
cd "C:\Users\aditya parashar\OneDrive\Desktop\Cyber"

# Activate environment and install dependencies
pip install -r backend/requirements.txt

# Run FastAPI with Uvicorn
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. SentinelX SOC Frontend (Port 5173)
```powershell
cd frontend
npm install
npm run dev
# Browser opens at http://localhost:5173
```

#### 3. NexaBank Digital Banking Frontend (Port 5174)
```powershell
cd ../banking-platform/frontend
npm install
npm run dev -- --port 5174
# Browser opens at http://localhost:5174
```

---

### Option B: Docker Compose (Air-Gapped / Evaluation)

To run the containerized stack:
```bash
# Build and start services in detached mode
docker compose up -d --build

# Verify running containers
docker compose ps

# Access URLs:
# - SentinelX SOC Workbench: http://localhost:3000
# - Backend API & OpenAPI Docs: http://localhost:8888/docs
```

---

## 4. Verification & Healthchecks

### 4.1 Core Backend Health
```bash
curl -f https://sentinelx-api-316t.onrender.com/health
# Expected: {"status":"healthy","database":"connected","version":"2.0.0"}
```

### 4.2 SOC Command Center System Health Matrix
```bash
curl -f https://sentinelx-api-316t.onrender.com/api/banking/command-center/stats
# Returns real metrics: total_events, active_incidents, active_storylines,
# threat_intel_matches, pending_approvals, successful_containments, failed_containments,
# and system_health matrix (db_status, ml_random_forest, ml_isolation_forest, storyline_correlator, uptime_seconds)
```

### 4.3 Unified Timeline Feed
```bash
curl -f https://sentinelx-api-316t.onrender.com/api/banking/command-center/timeline/unified?limit=10
# Returns ordered chronological event records across telemetry, transactions, violations, and response actions
```

### 4.4 Automated 13-Step Lifecycle Verification
```bash
curl -X POST https://sentinelx-api-316t.onrender.com/api/banking/demo/run-full-lifecycle \
  -H "Content-Type: application/json"
# Returns 13 passed lifecycle step verification records with sub-second execution latency
```

---

## 5. Deployment Rollout & Build Verification

Before triggering production deployments, execute the automated validation suite:

```bash
# 1. Run all 56 backend security & reliability tests
pytest tests/unit/ -v

# 2. Build SentinelX SOC frontend
cd frontend && npm run build && cd ..

# 3. Build NexaBank Banking frontend
cd banking-platform/frontend && npm run build && cd ..
```
All tests must pass (100% pass rate) and both frontends must compile with zero TypeScript or asset bundling errors.
