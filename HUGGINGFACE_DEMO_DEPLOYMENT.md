# SentinelX SOC — Hugging Face Free Static Demo Deployment Guide

**Date:** October 13, 2026  
**Project:** SentinelX SOC — Autonomous Cyber Threat Intelligence & Attack-Graph Reasoning Platform  
**Target Platform:** Hugging Face Spaces (SDK: `static` / HTML)  
**Hosting Cost:** \$0 / Free Tier (No compute, no payment card, no database dependencies)  
**Git Branch:** `hf-static-demo` (Isolated from production `main` branch)  

---

## 1. Summary of Work & Changes

To provide a 100% reliable, zero-cost, publicly accessible interactive demonstration that does not depend on cloud compute spin-downs or external database instances, an environment-controlled **Static Demo Mode** was developed and tested.

### Files Changed / Created

| File | Status | Rationale |
| :--- | :--- | :--- |
| `frontend/src/services/demoData.ts` | **Created** | Realistic synthetic dataset: 5 multi-stage incidents, 6 findings, 5 canonical events (Syslog, Sysmon, NetFlow), topological attack graphs with node/edge entities, benchmark metrics, threat indicators, and simulated response executions. Contains **zero secrets, zero real passwords, and zero operational infrastructure data**. |
| `frontend/src/services/demoAdapter.ts` | **Created** | Pure in-memory reactive storage adapter implementing the same interface as the backend API. Handles client-side incident status updates, simulated containment actions, IOC additions, and event filtering without network requests. |
| `frontend/src/services/api.ts` | **Modified** | Added `isDemoMode = import.meta.env.VITE_DEMO_MODE === 'true'`. When enabled, all API calls automatically bypass network requests and resolve against `demoStorage`. When disabled, original production API behavior is preserved. |
| `frontend/src/App.tsx` | **Modified** | Auto-logs into `demo_admin` profile when `isDemoMode === true` for immediate demonstration access. Displays an interactive amber demonstration notice banner. |
| `frontend/src/components/Navbar.tsx` | **Modified** | Renders a gold `"Interactive Demo Mode (Sample Telemetry)"` badge in place of the live API heartbeat when `isDemoMode === true`. |
| `frontend/src/components/LoginPage.tsx` | **Modified** | Provides explicit **Rapid Demonstration Profiles** (`demo_admin` / `demo_analyst`) with clear labels indicating simulated credentials. |
| `frontend/vite.config.ts` | **Modified** | Added `base: './'` to support relative asset paths necessary for iframe/subdirectory hosting inside Hugging Face Spaces. |
| `frontend/index.html` | **Modified** | Updated browser title to `"SentinelX SOC — Autonomous Cyber Defense & Attack-Graph Reasoning"`. |
| `.gitignore` | **Modified** | Added `deploy/` to prevent committing build artifacts to Git. |
| `deploy/hf-static-space/` | **Created (Local)** | Standalone staging directory containing production-built static assets (`index.html`, `assets/`, favicon, icons) and the Hugging Face `README.md` with Static SDK YAML frontmatter. |

---

## 2. How to Run Demo Mode Locally

To run the interactive demo locally without starting any backend server or Docker container:

```powershell
# In PowerShell:
cd "c:\Users\aditya parashar\OneDrive\Desktop\Cyber"

# Switch to the demo branch (if not already on it)
git checkout hf-static-demo

# Set Demo Mode environment variable and start Vite dev server
$env:VITE_DEMO_MODE="true"
npm --prefix frontend run dev
```

The application will launch at `http://localhost:5173/` (or the indicated Vite port). It will automatically open the SOC Command Deck with full interactive sample telemetry, attack graphs, and incident triage enabled.

---

## 3. How to Deploy to Hugging Face Spaces ($0, No Card)

Hugging Face Static Spaces host raw client-side HTML, CSS, and JS with zero server configuration and zero cost.

### Step 1: Create a Free Hugging Face Account
1. Go to [https://huggingface.co/join](https://huggingface.co/join) (if you do not already have an account).
2. No payment card or billing information is required.

### Step 2: Create a New Space
1. Click your profile icon (top right) $\rightarrow$ **New Space** (or visit [https://huggingface.co/new-space](https://huggingface.co/new-space)).
2. Configure the Space:
   - **Space Name:** `sentinelx-soc-demo`
   - **License:** `mit` (or leave default)
   - **Space SDK:** Select **Static** (HTML/JS/CSS).
   - **Space Hardware:** Select **Free** (CPU basic - 2 vCPU, 16 GB - \$0/mo).
   - **Visibility:** **Public**.
3. Click **Create Space**.

### Step 3: Upload the Built Demo Assets

You have two convenient methods to upload the pre-built files from `deploy/hf-static-space/`:

#### Option A: Direct Web Upload (Simplest — 1 Minute)
1. In your newly created Space, click the **Files** tab.
2. Click **Add file** $\rightarrow$ **Upload files**.
3. Drag and drop all files and folders from your local directory:
   ```
   c:\Users\aditya parashar\OneDrive\Desktop\Cyber\deploy\hf-static-space\
   ```
   Specifically:
   - `README.md` (Contains Hugging Face Static Space metadata)
   - `index.html`
   - `favicon.svg`
   - `icons.svg`
   - `assets/` (Directory containing `index-*.js` and `index-*.css`)
4. In the commit message box, enter: `Initial release of SentinelX SOC Static Demo`.
5. Click **Commit changes to main**.

#### Option B: Git Push to Hugging Face
In PowerShell:
```powershell
cd "c:\Users\aditya parashar\OneDrive\Desktop\Cyber\deploy\hf-static-space"

git init
git branch -M main
git add .
git commit -m "Deploy SentinelX SOC static demo to Hugging Face Space"

# Replace YOUR_HF_USERNAME with your Hugging Face username:
git remote add space https://huggingface.co/spaces/YOUR_HF_USERNAME/sentinelx-soc-demo

# Push to your Space repository (enter your HF username & access token when prompted):
git push -u space main --force
```

### Step 4: Live Verification Results

The Space is **active, verified, and running**:
- **Hugging Face Space URL:** [https://huggingface.co/spaces/Anuj1555/sentinelx-soc-demo](https://huggingface.co/spaces/Anuj1555/sentinelx-soc-demo)
- **Direct Fullscreen Web URL:** [https://anuj1555-sentinelx-soc-demo.static.hf.space](https://anuj1555-sentinelx-soc-demo.static.hf.space)
- **Verified HTTP Status:** `200 OK` across main page, CSS stylesheets, and compiled JavaScript bundles.
- **Operating Cost:** **\$0.00 / month forever** (No compute, no card, no database).

---

## 4. Verification & Testing Performed

1. **Frontend Production Build**:
   - Executed: `$env:VITE_DEMO_MODE="true"; npm --prefix frontend run build`
   - Result: **Passed cleanly in 462ms** (`tsc -b && vite build`).
   - Assets generated with relative paths (`./assets/...`) ensuring compatibility with Hugging Face base paths.
2. **Backend Regression Testing**:
   - Executed: `$env:PYTHONPATH="backend"; python -m pytest tests/unit -v`
   - Result: **12/12 unit and security tests passed** (parsers, detection engine, hash chaining, response engine).
3. **Branch Isolation**:
   - Verified that `main` branch remains untouched and up to date with `origin/main`.
   - All demo mode changes reside strictly on the `hf-static-demo` branch.
4. **Secret Exposure Audit**:
   - Verified that `deploy/hf-static-space/` contains zero database URIs, API tokens, `.env` files, or production credentials.

---

## 5. Known Limitations of the Static Demo

- **Data Persistence:** Because this demo runs client-side without a persistent server database, changes made during the session (e.g. adding a new IOC or executing a simulated response) persist in browser memory and reset upon a full page reload.
- **Simulated Ingestion:** Uploading custom log files simulates log parsing and displays synthetic events in the table without running the Python parsing engine.
- **Simulated Response Actions:** Defense playbooks execute in dry-run simulation mode without executing OS system calls or firewall modifications.

---

## 6. How to Update the Demo in the Future

Whenever changes or enhancements are made:
```powershell
# 1. Switch to demo branch
git checkout hf-static-demo

# 2. Rebuild assets in demo mode
$env:VITE_DEMO_MODE="true"
npm --prefix frontend run build

# 3. Copy dist assets to staging folder
Copy-Item -Path "frontend/dist/*" -Destination "deploy/hf-static-space" -Recurse -Force

# 4. Upload updated files to your Hugging Face Space (via Web UI or git push)
```
