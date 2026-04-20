"""Connect without a database and ask the server what's available."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pyodbc
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

HOST = os.environ["SPECTRUM_SQL_HOST"]
PORT = os.environ.get("SPECTRUM_SQL_PORT", "1433")
USER = os.environ["SPECTRUM_SQL_USER"]
PWD = os.environ["SPECTRUM_SQL_PASSWORD"]

# No DATABASE= in the string → login uses its default.
CONN_STR = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={HOST},{PORT};UID={USER};PWD={PWD};"
    "Encrypt=yes;TrustServerCertificate=yes;"
)

print(f"Connecting to {HOST}:{PORT} as {USER} (no DB specified)…")
conn = pyodbc.connect(CONN_STR, timeout=10, readonly=True)
cur = conn.cursor()

cur.execute("SELECT DB_NAME() AS current_db, SUSER_NAME() AS login_name, @@SERVERNAME AS server")
r = cur.fetchone()
print(f"\nConnected.")
print(f"  Current (default) DB : {r.current_db}")
print(f"  Login name           : {r.login_name}")
print(f"  Server name          : {r.server}")

print("\nDatabases this login can see:")
cur.execute("""
    SELECT name FROM sys.databases
    WHERE HAS_DBACCESS(name) = 1
    ORDER BY name
""")
for row in cur.fetchall():
    print(f"  - {row.name}")
