# SentinelX SOC & Banking Gateway — Demonstration Guide

This guide provides end-to-end instructions for testing and demonstrating the SentinelX SOC platform and the integrated Banking Security Gateway.

---

## 1. Accessing the Platform

- **Production Frontend:** `https://frontend-sigma-liart-89.vercel.app/`
- **Static Hugging Face Space Demo:** `https://anuj1555-sentinelx-soc-demo.static.hf.space`
- **Backend API Docs:** `https://sentinelx-api-316t.onrender.com/docs`
- **Default Demonstration Credentials:**
  - Username: `admin`
  - Password: `Admin@SentinelX2026`

---

## 2. Banking Simulation Demonstration Scenarios

Navigate to the **Banking Simulation** tab from the left sidebar navigation.

### Scenario 1: Clean Transfer (`ALLOW` $\to$ `POSTED`)
1. Click the preset button **"1. Clean Normal"** (or enter Amount: `5000`, Destination: `ACT-SYNTH-2002`).
2. Click **"Evaluate Risk & Process Transfer"**.
3. **Observed Outcome:**
   - Policy Decision: `ALLOW (Cleared)` (Risk Score: `0 / 100`).
   - Status: `POSTED`.
   - The Monitored Bank Accounts card updates immediately: source account is debited ₹5,000.00 and destination account is credited ₹5,000.00.
   - An immutable record appears in the Transaction Ledger table.

---

### Scenario 2: High Amount Step-Up Challenge (`VERIFY` $\to$ `POSTED`)
1. Click the preset button **"2. Step-Up OTP"** (Amount: `250000`, Destination: `ACT-SYNTH-2002`).
2. Click **"Evaluate Risk & Process Transfer"**.
3. **Observed Outcome:**
   - Policy Decision: `VERIFY (Step-Up)` (Risk Score: `45 / 100`).
   - Status: `AWAITING_VERIFICATION`.
   - Reason Code: `HIGH_AMOUNT_THRESHOLD`.
   - Notice that **no funds have been debited yet**.
   - A 2FA Step-Up Passcode prompt appears in the inspector card.
4. Enter the demonstration OTP: **`123456`** and click **"Confirm Code"**.
5. **Observed Outcome:**
   - Challenge clears, transfer transitions to `POSTED`, and funds are debited from source and credited to destination.

---

### Scenario 3: Critical High Value Flag (`HOLD`)
1. Click the preset button **"3. Critical High"** (Amount: `600000`, Destination: `ACT-SYNTH-2002`).
2. Click **"Evaluate Risk & Process Transfer"**.
3. **Observed Outcome:**
   - Policy Decision: `HOLD (Review)` (Risk Score: `85 / 100`).
   - Status: `HELD`.
   - Reason Code: `CRITICAL_AMOUNT_THRESHOLD`.
   - Balances remain completely untouched.
   - A canonical security event is emitted to the SentinelX SOC stream.

---

### Scenario 4: Suspended Destination Account (`BLOCK`)
1. Click the preset button **"4. Suspended Target"** (Amount: `1000`, Destination: `ACT-SYNTH-9999`).
2. Click **"Evaluate Risk & Process Transfer"**.
3. **Observed Outcome:**
   - Policy Decision: `BLOCK (Denied)` (Risk Score: `100 / 100`).
   - Status: `BLOCKED`.
   - Reason Code: `DESTINATION_ACCOUNT_RESTRICTED`.
   - An actionable Incident is generated in SentinelX SOC.
4. Navigate to the **Incidents & Triage** tab in the sidebar to view the newly created incident, evidence events, and affected entity graphs.

---

### Scenario 5: Idempotency Replay Protection
1. Copy the current **Idempotency Protection Key** displayed in the transfer panel.
2. Submit a transfer.
3. Without regenerating the key, immediately click **"Evaluate Risk & Process Transfer"** again with identical values.
4. **Observed Outcome:**
   - The gateway recognizes the reused key and returns the identical previous transaction record without debiting the account a second time.
