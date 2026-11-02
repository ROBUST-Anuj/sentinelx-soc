import os
import uuid
import pytest
import httpx

TARGET_API_URL = os.getenv("TARGET_API_URL", "https://sentinelx-api-316t.onrender.com").rstrip("/")
ADMIN_USERNAME = os.getenv("PROD_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("PROD_ADMIN_PASSWORD", "Admin@SentinelX2026")
ANALYST_USERNAME = os.getenv("PROD_ANALYST_USERNAME", "analyst")
ANALYST_PASSWORD = os.getenv("PROD_ANALYST_PASSWORD", "Analyst@SentinelX2026")

CLIENT_TIMEOUT = 90.0  # Accounts for cloud PaaS cold-starts and e2e multi-step scenarios

@pytest.mark.asyncio
async def test_live_production_health():
    """Verify production backend health and version."""
    async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
        res = await client.get(f"{TARGET_API_URL}/health")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "healthy"
        assert "version" in data
        assert "service" in data


@pytest.mark.asyncio
async def test_live_production_auth_admin():
    """Verify administrator authentication against live production backend."""
    async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
        res = await client.post(
            f"{TARGET_API_URL}/api/auth/login",
            data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data.get("role") == "admin"


@pytest.mark.asyncio
async def test_live_production_auth_analyst():
    """Verify SOC analyst authentication against live production backend."""
    async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
        res = await client.post(
            f"{TARGET_API_URL}/api/auth/login",
            data={"username": ANALYST_USERNAME, "password": ANALYST_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data.get("role") == "analyst"


@pytest.mark.asyncio
async def test_live_production_cors_preflight_nexabank():
    """Verify CORS preflight OPTIONS requests from NexaBank origin succeed with 200 OK."""
    async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
        headers = {
            "Origin": "https://nexabank-portal.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        }
        res = await client.options(f"{TARGET_API_URL}/api/auth/login", headers=headers)
        assert res.status_code == 200
        assert "access-control-allow-origin" in res.headers or "access-control-allow-credentials" in res.headers


@pytest.mark.asyncio
async def test_live_production_auth_json():
    """Verify authentication succeeds when payload is transmitted as JSON."""
    async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
        res = await client.post(
            f"{TARGET_API_URL}/api/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            headers={"Origin": "https://nexabank-portal.vercel.app"}
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data.get("role") == "admin"


@pytest.mark.asyncio
async def test_live_production_account_retrieval():
    """Verify synthetic bank account retrieval for authenticated user."""
    async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
        # 1. Login
        login_res = await client.post(
            f"{TARGET_API_URL}/api/auth/login",
            data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get accounts
        acc_res = await client.get(f"{TARGET_API_URL}/api/banking/accounts", headers=headers)
        assert acc_res.status_code == 200
        accounts = acc_res.json()
        assert len(accounts) > 0
        assert any(acc["account_number"] == "ACT-SYNTH-1001" for acc in accounts)


@pytest.mark.asyncio
async def test_live_production_safe_synthetic_transfer():
    """Execute a safe, non-destructive synthetic micro-transfer between demo accounts."""
    async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
        # 1. Login
        login_res = await client.post(
            f"{TARGET_API_URL}/api/auth/login",
            data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Retrieve source account
        acc_res = await client.get(f"{TARGET_API_URL}/api/banking/accounts", headers=headers)
        assert acc_res.status_code == 200
        accounts = acc_res.json()
        source_acc = next((a for a in accounts if a["account_number"] == "ACT-SYNTH-1001"), None)
        assert source_acc is not None, "Source synthetic account ACT-SYNTH-1001 not found"

        # 3. Initiate safe micro-transfer to ACT-SYNTH-2002 (₹1.00 = 100 paise)
        tx_payload = {
            "source_account_id": source_acc["id"],
            "destination_account_number": "ACT-SYNTH-2002",
            "amount_minor": 100,
            "currency": "INR",
            "description": "Automated Live Production Verification Test",
            "idempotency_key": f"prod-verify-{uuid.uuid4().hex[:12]}"
        }

        tx_res = await client.post(
            f"{TARGET_API_URL}/api/banking/transfers",
            json=tx_payload,
            headers=headers
        )
        assert tx_res.status_code == 200
        tx_data = tx_res.json()
        assert tx_data["status"] in ["POSTED", "AWAITING_VERIFICATION"]
        assert tx_data["amount_minor"] == 100


@pytest.mark.asyncio
async def test_live_production_blocked_transfer_invariant():
    """Verify that attempting transfer to restricted account ACT-SYNTH-9999 is blocked with zero fund leakage."""
    async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
        # 1. Login
        login_res = await client.post(
            f"{TARGET_API_URL}/api/auth/login",
            data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Retrieve source account
        acc_res = await client.get(f"{TARGET_API_URL}/api/banking/accounts", headers=headers)
        assert acc_res.status_code == 200
        accounts = acc_res.json()
        source_acc = next((a for a in accounts if a["account_number"] == "ACT-SYNTH-1001"), None)
        assert source_acc is not None

        # 3. Transfer to ACT-SYNTH-9999 (Restricted/Suspicious Account)
        tx_payload = {
            "source_account_id": source_acc["id"],
            "destination_account_number": "ACT-SYNTH-9999",
            "amount_minor": 500_00,
            "currency": "INR",
            "description": "Restricted Account Live Block Test",
            "idempotency_key": f"prod-block-{uuid.uuid4().hex[:12]}"
        }

        tx_res = await client.post(
            f"{TARGET_API_URL}/api/banking/transfers",
            json=tx_payload,
            headers=headers
        )
        assert tx_res.status_code == 200
        tx_data = tx_res.json()
        assert tx_data["status"] == "BLOCKED"
        assert tx_data["policy_decision"] == "BLOCK"


@pytest.mark.asyncio
async def test_live_production_command_center_metrics():
    """Verify live SOC command center metrics endpoint returns non-empty persistent counters."""
    async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
        # 1. Login as Analyst
        login_res = await client.post(
            f"{TARGET_API_URL}/api/auth/login",
            data={"username": ANALYST_USERNAME, "password": ANALYST_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Retrieve SOC Stats
        stats_res = await client.get(
            f"{TARGET_API_URL}/api/banking/command-center/stats",
            headers=headers
        )
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert "total_security_events" in stats
        assert "active_critical_high_incidents" in stats
        assert "active_attack_storylines" in stats
        assert "active_threat_indicators" in stats


@pytest.mark.asyncio
async def test_live_production_full_lifecycle_demo():
    """Verify live execution of the 13-step NexaBank-to-SentinelX attack and defense lifecycle."""
    async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
        # 1. Login as Admin
        login_res = await client.post(
            f"{TARGET_API_URL}/api/auth/login",
            data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Run 13-step lifecycle
        demo_res = await client.post(
            f"{TARGET_API_URL}/api/banking/command-center/demo/run-full-lifecycle",
            headers=headers
        )
        assert demo_res.status_code == 200
        demo_data = demo_res.json()
        assert demo_data["total_steps"] == 13
        assert demo_data["successful_steps"] == 13
        assert demo_data["customer_id"] == "cust-e2e-demo"
        assert len(demo_data["steps"]) == 13
