import sqlite3

conn = sqlite3.connect('data/sentinelx.db')
c = conn.cursor()

c.execute("PRAGMA table_info(audit_logs)")
existing_cols = [row[1] for row in c.fetchall()]
print("Current columns:", existing_cols)

if "prev_hash" not in existing_cols:
    c.execute("ALTER TABLE audit_logs ADD COLUMN prev_hash VARCHAR")
    print("Added prev_hash column")

if "entry_hash" not in existing_cols:
    c.execute("ALTER TABLE audit_logs ADD COLUMN entry_hash VARCHAR DEFAULT ''")
    print("Added entry_hash column")

conn.commit()
c.execute("PRAGMA table_info(audit_logs)")
print("Updated columns:", [row[1] for row in c.fetchall()])
