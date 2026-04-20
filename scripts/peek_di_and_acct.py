"""Peek at Spectrum DI (document imaging) tables and the accounting NAS share."""
import os, sys
from pathlib import Path
import pyodbc
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={os.environ['SPECTRUM_SQL_HOST']},1433;"
    f"DATABASE={os.environ['SPECTRUM_SQL_DATABASE']};"
    f"UID={os.environ['SPECTRUM_SQL_USER']};PWD={os.environ['SPECTRUM_SQL_PASSWORD']};"
    "Encrypt=yes;TrustServerCertificate=yes;ApplicationIntent=ReadOnly;",
    timeout=10, readonly=True,
)
cur = conn.cursor()

for sql, label in [
    ("SELECT TOP 5 * FROM dbo.DI_MASTER_MC WHERE Company_Code = 'AA1'", "DI_MASTER_MC sample"),
    ("SELECT TOP 5 * FROM dbo.DI_IMAGE_XREF", "DI_IMAGE_XREF sample"),
    ("SELECT COUNT(*) AS n FROM dbo.DI_MASTER_MC WHERE Company_Code = 'AA1'", "DI rows for AA1"),
    ("SELECT TOP 5 * FROM dbo.DI_IMAGE_MASTER", "DI_IMAGE_MASTER sample"),
    ("SELECT DISTINCT TOP 20 Cabinet FROM dbo.DI_MASTER_MC WHERE Company_Code = 'AA1'", "DI Cabinets"),
    ("SELECT DISTINCT TOP 20 Drawer FROM dbo.DI_MASTER_MC WHERE Company_Code = 'AA1'", "DI Drawers"),
]:
    print(f"\n== {label} ==")
    try:
        cur.execute(sql)
        if cur.description:
            cols = [c[0] for c in cur.description]
            print(" | ".join(cols))
            for row in cur.fetchall():
                print(" | ".join(str(v)[:60] for v in row))
    except Exception as e:
        print(f"ERROR: {e}")

# Also peek at accounting share top-level structure
import os as _os
print("\n\n== Accounting share top-level ==")
acct = Path("C:/nas/accounting")
if acct.exists():
    for entry in sorted(acct.iterdir())[:30]:
        kind = "DIR " if entry.is_dir() else "FILE"
        print(f"  {kind} {entry.name}")
