# NexaBank Vercel Deployment Diagnostic & Remediation Report

**Date of Resolution:** November 03, 2026  
**Status:** **RESOLVED & VERIFIED IN PRODUCTION**  
**Repository:** `https://github.com/ROBUST-Anuj/sentinelx-soc`  
**Target Branch:** `main`  
**Deploy Commit:** [`4d87551`](https://github.com/ROBUST-Anuj/sentinelx-soc/commit/4d87551)  

---

## 1. Executive Summary & Production Status

| Application | Production URL | Branding & Page Title | Active JS Bundle | Status |
|---|---|---|---|:---:|
| **NexaBank Customer Portal** | [`https://nexabank-portal.vercel.app/`](https://nexabank-portal.vercel.app/) | `NexaBank \| Modern Digital Banking` | `/assets/index-JsVaJS8c.js` | **LIVE & INDEPENDENT** |
| **SentinelX SOC Console** | [`https://frontend-sigma-liart-89.vercel.app/`](https://frontend-sigma-liart-89.vercel.app/) | `SentinelX SOC Platform` | `/assets/index-BXWsCiqN.js` | **LIVE & INDEPENDENT** |
| **Shared API Backend** | [`https://sentinelx-api-316t.onrender.com`](https://sentinelx-api-316t.onrender.com) | Core API (v2.2.0) | FastAPI + PostgreSQL | **HEALTHY** |

---

## 2. Root Cause Analysis

### 2.1 The Issue
Both `https://nexabank-portal.vercel.app/` and `https://frontend-sigma-liart-89.vercel.app/` were previously displaying the SentinelX SOC console login screen.

### 2.2 Forensic Inspection
We inspected the cloud project settings for Vercel Project `nexabank-portal` (Project ID: `prj_Ul5QiT01ZqAGAdo7cTNuAIxvzIAj` under team `robust-anuj`) via the Vercel REST API:

```json
{
  "id": "prj_Ul5QiT01ZqAGAdo7cTNuAIxvzIAj",
  "name": "nexabank-portal",
  "rootDirectory": "frontend",
  "framework": "vite",
  "buildCommand": null,
  "outputDirectory": null,
  "targets": {
    "production": {
      "alias": ["nexabank-portal.vercel.app"]
    }
  }
}
```

### 2.3 The Fault
The Vercel project `nexabank-portal` was configured with:
$$\text{rootDirectory} = \mathbf{"frontend"}$$
This caused Vercel to build the SentinelX SOC application (`frontend/`) and deploy its build output to `nexabank-portal.vercel.app`.

---

## 3. Remediation Executed

### 3.1 Vercel Project Setting Correction
We updated `nexabank-portal` via the Vercel REST API:
- **`rootDirectory`:** Changed from `frontend` to `banking-platform/frontend`
- **`framework`:** Explicitly set to `vite`
- **`buildCommand`:** Set to `npm run build`
- **`outputDirectory`:** Set to `dist`
- **`VITE_API_BASE_URL`:** Verified and persisted as `https://sentinelx-api-316t.onrender.com` across `production`, `preview`, and `development` targets.

### 3.2 NexaBank SPA Routing Hardening
In `banking-platform/frontend/src/App.tsx` and `Navbar.tsx`:
- Added support for all specified SPA routes:
  - `/login`: Dedicated customer banking login interface.
  - `/dashboard`: Primary customer dashboard with balance, account numbers, and quick actions.
  - `/accounts`: Synchronized alias for account statements and ledger history.
  - `/transfer`: Step-up fraud gateway and beneficiary transfer interface.
  - `/transactions`: Real-time transaction history and receipt inspector.
  - `/profile`: Dedicated customer profile card displaying account tier, limits, multi-layer security protections, and session telemetry.
- Configured browser history pushState and popstate event listeners.
- Preserved Vercel client-side rewrites in `banking-platform/frontend/vercel.json`:
  ```json
  {
    "rewrites": [
      {
        "source": "/(.*)",
        "destination": "/index.html"
      }
    ]
  }
  ```

---

## 4. Production Build & Deployment Logs

### 4.1 NexaBank Build Log (`banking-platform/frontend`)
```
> nexabank-frontend@1.0.0 build
> tsc -b && vite build

vite v6.4.5 building for production...
transforming...
✓ 1659 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.83 kB │ gzip:   0.48 kB
dist/assets/index-CNULHlcq.css   44.45 kB │ gzip:   7.54 kB
dist/assets/index-JsVaJS8c.js   352.79 kB │ gzip: 107.85 kB
✓ built in 2.07s
```

### 4.2 Vercel Cloud Deployment Record
- **Deployment ID:** `dpl_DKKBiwh9ZsBR1JJc61ehtgncBXvL`
- **Commit:** `4d87551`
- **Target URL:** `https://nexabank-portal.vercel.app`
- **State:** `READY`

---

## 5. Live Production Verification Results

### 5.1 HTTP Status & Metadata Probe
- **Target:** `https://nexabank-portal.vercel.app/`
- **HTTP Status:** `200 OK`
- **HTML `<title>`:** `NexaBank | Modern Digital Banking`
- **Loaded JavaScript Bundle:** `/assets/index-JsVaJS8c.js`
- **Loaded CSS Bundle:** `/assets/index-CNULHlcq.css`
- **Branding:** NexaBank Premier Digital Banking

- **Target:** `https://frontend-sigma-liart-89.vercel.app/`
- **HTTP Status:** `200 OK`
- **HTML `<title>`:** `frontend` (SentinelX SOC)
- **Loaded JavaScript Bundle:** `/assets/index-BXWsCiqN.js`
- **Loaded CSS Bundle:** `/assets/index-BbC7xzyh.css`
- **Branding:** SentinelX SOC Operations Console

### 5.2 Direct Route Refresh & Deep Linking Tests
Automated probes confirmed every route serves `index.html` with full 200 OK status:
- `GET https://nexabank-portal.vercel.app/login` -> **200 OK** (NexaBank title verified)
- `GET https://nexabank-portal.vercel.app/dashboard` -> **200 OK** (NexaBank title verified)
- `GET https://nexabank-portal.vercel.app/accounts` -> **200 OK** (NexaBank title verified)
- `GET https://nexabank-portal.vercel.app/transfer` -> **200 OK** (NexaBank title verified)
- `GET https://nexabank-portal.vercel.app/transactions` -> **200 OK** (NexaBank title verified)
- `GET https://nexabank-portal.vercel.app/profile` -> **200 OK** (NexaBank title verified)

---

## 6. Production Application Screenshots

Headless browser captures of both production deployments:

| Application | Production URL | Screenshot Artifact |
|---|---|---|
| **NexaBank Customer Portal** | `https://nexabank-portal.vercel.app/` | `docs/screenshots/nexabank_portal.png` |
| **SentinelX SOC Workbench** | `https://frontend-sigma-liart-89.vercel.app/` | `docs/screenshots/sentinelx_soc.png` |

---

## 7. Remaining Issues

None. Both applications are completely decoupled, properly routed, and live in production with independent branding, distinct bundles, and verified backend connectivity.
