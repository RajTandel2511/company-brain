"""Does Spectrum DI already store OCR'd text we can lift directly?"""
import os
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

print("=== 1) DI_FULL_TEXT_MC columns ===")
cur.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'DI_FULL_TEXT_MC' ORDER BY ORDINAL_POSITION
""")
for row in cur.fetchall():
    print(f"  {row.COLUMN_NAME:<30} {row.DATA_TYPE}({row.CHARACTER_MAXIMUM_LENGTH})")

print("\n=== 2) DI_FULL_TEXT_MC row count for AA1 ===")
try:
    cur.execute("SELECT COUNT(*) FROM dbo.DI_FULL_TEXT_MC WHERE Company_Code = 'AA1'")
    print(f"  rows for AA1: {cur.fetchone()[0]:,}")
except Exception as e:
    # Company_Code might not be on this table — try a generic count
    cur.execute("SELECT COUNT(*) FROM dbo.DI_FULL_TEXT_MC")
    print(f"  total rows: {cur.fetchone()[0]:,}  (no Company_Code filter)")

print("\n=== 3) Sample row with truncated text ===")
cur.execute("SELECT TOP 3 * FROM dbo.DI_FULL_TEXT_MC")
cols = [c[0] for c in cur.description]
for row in cur.fetchall():
    for name, value in zip(cols, row):
        v = str(value)[:200]
        print(f"  {name:<30} = {v!r}")
    print()

print("=== 4) Can we join DI_FULL_TEXT_MC back to DI_IMAGE_MASTER? ===")
# Look for join keys — typically Document_ID or Transaction_ID
cur.execute("""
    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'DI_FULL_TEXT_MC'
      AND COLUMN_NAME IN ('Document_ID','Transaction_ID','Image_ID','Doc_ID')
""")
join_cols = [r.COLUMN_NAME for r in cur.fetchall()]
print(f"  Possible join keys on FULL_TEXT_MC: {join_cols}")

print("\n=== 5) DI_FULL_TEXT_TABLE (if it's the real content) ===")
try:
    cur.execute("""
        SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'DI_FULL_TEXT_TABLE'
    """)
    for row in cur.fetchall():
        print(f"  {row.COLUMN_NAME}  {row.DATA_TYPE}")
    cur.execute("SELECT COUNT(*) FROM dbo.DI_FULL_TEXT_TABLE")
    print(f"  rows: {cur.fetchone()[0]:,}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n=== 6) DI_CACHE_LOCATION_MC — where images are cached ===")
try:
    cur.execute("SELECT TOP 5 * FROM dbo.DI_CACHE_LOCATION_MC")
    cols = [c[0] for c in cur.description]
    for row in cur.fetchall():
        d = dict(zip(cols, row))
        print(f"  {d}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n=== 7) DI_PATH_ALLOC_INQ — allocation of image paths ===")
try:
    cur.execute("SELECT TOP 5 * FROM dbo.DI_PATH_ALLOC_INQ")
    cols = [c[0] for c in cur.description]
    for row in cur.fetchall():
        d = dict(zip(cols, row))
        print(f"  {d}")
except Exception as e:
    print(f"  ERROR: {e}")
