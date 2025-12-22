import sqlite3
from pathlib import Path

db = Path(__file__).parent.parent / ".phoenix_data" / "phoenix_traces.db"
print(f"DB: {db}")
print(f"Exists: {db.exists()}")

if db.exists():
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = c.fetchall()
    print("\nTables:")
    for t in tables:
        print(f"  - {t[0]}")
        # Show schema
        c.execute(f"PRAGMA table_info({t[0]})")
        cols = c.fetchall()
        for col in cols:
            print(f"      {col[1]} ({col[2]})")
    conn.close()
