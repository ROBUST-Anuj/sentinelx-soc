# NexaBank Vercel Deployment Diagnostic & Remediation Report

**Date:** November 03, 2026  
**Auditor:** Senior DevSecOps & Production Release Engineering  
**Repository:** `https://github.com/ROBUST-Anuj/sentinelx-soc`  
**Branch:** `main`  
**Issue Under Investigation:** `https://nexabank-portal.vercel.app/` serving SentinelX SOC instead of NexaBank  

---

## 1. Executive Summary & Root Cause Diagnosis

### 1.1 The Reported Production Issue
When visiting:
- **SentinelX SOC URL:** `https://frontend-sigma-liart-89.vercel.app/`
- **NexaBank Portal URL:** `https://nexabank-portal.vercel.app/`

Both domains were displaying the SentinelX SOC login screen (`<title>frontend</title>`, bundle `index-D3uUo7HO.js` / `index-CEzOrNaS.css`).

### 1.2 Exact Root Cause Identified
We audited the live Vercel Cloud project configuration via the Vercel API for Project `nexabank-portal` (`prj_Ul5QiT01ZqAGAdo7cTNuAIxvzIAj` under team `robust-anuj`):

```json
{
  "id": "prj_Ul5QiT01ZqAGAdo7cTNuAIxvzIAj",
  "name": "nexabank-portal",
  "rootDirectory": "frontend",
  "framework": "vite",
  "buildCommand": null,
  "outputDirectory": null,
  "link": {
    "type": "github",
    "repo": "sentinelx-soc",
    "org": "ROBUST-Anuj",
    "productionBranch": "main"
  }
}
```

**Root Cause:**  
The Vercel project `nexabank-portal` was configured with:
$$\text{rootDirectory} = \mathbf{"frontend"}$$

Because the root directory pointed to `frontend` (which is the SentinelX SOC codebase) instead of `banking-platform/frontend`, Vercel executed Vite inside `frontend/` on every commit to `main`. Consequently, the SentinelX SOC application bundle was generated and deployed to `https://nexabank-portal.vercel.app/`.

---

## 2. NexaBank Frontend Verification (`banking-platform/frontend`)

### 2.1 Package & Scripts Verification
- **Directory:** `banking-platform/frontend`
- **Package Name:** `nexabank-frontend` (v1.0.0)
- **Framework:** React 19.0.0 + Vite 6.2.0 + TailwindCSS v4
- **Build Script:** `"build": "tsc -b && vite build"`

### 2.2 Local Production Build Output
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
✓ built in 2.06s
```

### 2.3 HTML & Assets Inspection
Inspection of `banking-platform/frontend/dist/index.html` confirms:
- **Page Title:** `<title>NexaBank | Modern Digital Banking</title>`
- **Font:** Google Fonts `Plus Jakarta Sans`
- **Branding:** NexaBank Premier Digital Banking
- **Zero SOC References:** No SentinelX SOC dashboard, operator auth, or incident response code in the banking client.

---

## 3. SPA Routing Implementation

To satisfy Step 4, `banking-platform/frontend/src/App.tsx` and `Navbar.tsx` have been updated with full client-side route synchronization:

| Route Path | View Rendered | Behavior on Direct Refresh |
|---|---|---|
| `/login` | `LoginPage` | Unauthenticated customer banking login; redirects to `/dashboard` if session active |
| `/dashboard` | `DashboardPage` | Account overview, quick balance, transfer button, recent activity |
| `/accounts` | `DashboardPage` | Synchronized alias for customer banking accounts |
| `/transfer` | `TransferPage` | Pre-transaction fraud gateway, beneficiary selection, amount input |
| `/transactions` | `TransactionsPage` | Double-entry ledger audit trail, downloadable receipts |
| `/profile` | `ProfilePage` | Dedicated customer profile, deposit insurance, banking tier, security features |

### Vercel SPA Fallback Configuration
In `banking-platform/frontend/vercel.json`:
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
Direct browser reloads and deep links (`/transfer`, `/transactions`, `/profile`) resolve to `/index.html` without 404 errors or redirection to SentinelX.

---

## 4. Corrected Vercel Project Settings for `nexabank-portal`

The exact Vercel project configuration required:

| Setting | Required Value | Current Misconfigured Value | Status |
|---|---|---|:---:|
| **Project Name** | `nexabank-portal` | `nexabank-portal` | Correct |
| **Root Directory** | `banking-platform/frontend` | `frontend` | **FIX REQUIRED** |
| **Framework Preset** | `Vite` | `Vite` | Correct |
| **Build Command** | `npm run build` | Default (`npm run build`) | Correct |
| **Output Directory** | `dist` | Default (`dist`) | Correct |
| **Node.js Version** | `24.x` or `26.x` | `26.x` | Correct |
| **Environment Variables** | `VITE_API_BASE_URL=https://sentinelx-api-316t.onrender.com` | `VITE_API_BASE_URL` | Correct |
| **Domain** | `nexabank-portal.vercel.app` | `nexabank-portal.vercel.app` | Correct |

---

## 5. Remediation & Deployment Plan

Pursuant to the strict rule:
> *"Do not push or deploy without explicit authorization."*

The following actions are prepared and ready for execution upon user authorization:

1. **Update Vercel Project Root Directory:**
   Send `PATCH /v9/projects/nexabank-portal` via Vercel API (or via Vercel Dashboard Settings -> General -> Root Directory) setting `rootDirectory: "banking-platform/frontend"`.
2. **Commit & Push SPA Route Enhancements:**
   Commit the added `ProfilePage.tsx` and updated `App.tsx` & `Navbar.tsx` to `main`.
3. **Trigger Production Redeployment:**
   Trigger a production deployment on Vercel so `nexabank-portal` builds strictly from `banking-platform/frontend`.
4. **Live Verification & Proof:**
   Fetch `https://nexabank-portal.vercel.app/` and confirm title is `NexaBank | Modern Digital Banking` and bundle is `nexabank-frontend`.
