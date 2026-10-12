import sqlite3
import hashlib
from datetime import datetime

conn = sqlite3.connect('data/sentinelx.db')
c = conn.cursor()
c.execute("SELECT id, user_id, action, resource_type, resource_id, prev_hash, entry_hash, timestamp FROM audit_logs ORDER BY timestamp ASC")
rows = c.fetchall()
print(f"Total Audit Logs: {len(rows)}")

def verify_chain(record_list):
    for i, row in enumerate(record_list):
        entry_id, user_id, action, res_type, res_id, prev_hash, entry_hash, ts_str = row
        dt = datetime.fromisoformat(ts_str) if isinstance(ts_str, str) else ts_str
        payload = f"{prev_hash or 'GENESIS'}|{user_id}|{action}|{res_type}|{res_id or ''}|{dt.isoformat()}"
        calc_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if calc_hash != entry_hash:
            return False, i, f"Hash mismatch at index {i}: expected {entry_hash}, got {calc_hash}"
        if i > 0 and prev_hash != record_list[i-1][6]:
            return False, i, f"Chain linkage broken at index {i}: prev_hash {prev_hash} != previous entry_hash {record_list[i-1][6]}"
    return True, len(record_list), "All hashes cryptographically verified"

valid, count, msg = verify_chain(rows)
print(f"Audit Log Hash-Chain Verification Result: {valid} ({msg})")

# Tamper simulation test
if len(rows) > 0:
    tampered_rows = [list(r) for r in rows]
    # Mutate the action field of the first record
    tampered_rows[0][2] = "MALICIOUS_UNAUTHORIZED_MUTATION"
    tampered_valid, _, tamper_msg = verify_chain([tuple(r) for r in tampered_rows])
    print(f"Tamper Detection Test: Successfully caught tampering = {not tampered_valid} ({tamper_msg})")
