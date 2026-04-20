"""Figure out where Spectrum actually stores the scanned image data."""
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

print("=== 1) All tables with 'IMAGE' or 'DI_' in the name ===")
cur.execute("""
    SELECT TABLE_SCHEMA, TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE (TABLE_NAME LIKE '%IMAGE%' OR TABLE_NAME LIKE 'DI_%')
      AND TABLE_SCHEMA = 'dbo'
    ORDER BY TABLE_NAME
""")
tables = [(s, t) for s, t in cur.fetchall()]
for s, t in tables:
    print(f"  {s}.{t}")

print("\n=== 2) Any BLOB (varbinary / image) columns in these tables ===")
for s, t in tables:
    cur.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
          AND DATA_TYPE IN ('varbinary','binary','image','text','ntext')
    """, (s, t))
    for row in cur.fetchall():
        print(f"  {s}.{t}.{row.COLUMN_NAME}  {row.DATA_TYPE}({row.CHARACTER_MAXIMUM_LENGTH})")

print("\n=== 3) DI_IMAGE_MASTER: what % have Image_Path populated? ===")
cur.execute("""
    SELECT
        COUNT(*) AS total,
        SUM(CASE WHEN Image_Path IS NOT NULL AND LEN(LTRIM(RTRIM(Image_Path))) > 0 THEN 1 ELSE 0 END) AS with_path,
        SUM(CASE WHEN Image_Filename IS NOT NULL AND LEN(LTRIM(RTRIM(Image_Filename))) > 0 THEN 1 ELSE 0 END) AS with_filename
    FROM dbo.DI_IMAGE_MASTER
""")
row = cur.fetchone()
print(f"  rows: {row.total}, with Image_Path: {row.with_path}, with Image_Filename: {row.with_filename}")

print("\n=== 4) Sample Image_Path values that ARE populated ===")
cur.execute("""
    SELECT TOP 10 Image_Path, Image_Filename, Image_Description
    FROM dbo.DI_IMAGE_MASTER
    WHERE Image_Path IS NOT NULL AND LEN(LTRIM(RTRIM(Image_Path))) > 0
""")
for row in cur.fetchall():
    print(f"  path={row.Image_Path!r}  file={row.Image_Filename!r}")

print("\n=== 5) Search ENTIRE database for any BLOB columns ===")
cur.execute("""
    SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE DATA_TYPE IN ('varbinary','binary','image')
      AND TABLE_SCHEMA = 'dbo'
    ORDER BY TABLE_NAME
""")
blobs = cur.fetchall()
print(f"  Found {len(blobs)} BLOB columns across the DB")
for r in blobs[:30]:
    print(f"  {r.TABLE_NAME}.{r.COLUMN_NAME}  {r.DATA_TYPE}({r.CHARACTER_MAXIMUM_LENGTH})")

print("\n=== 6) Do any of those BLOB tables look like image storage? ===")
for r in blobs:
    if "image" in r.TABLE_NAME.lower() or "doc" in r.TABLE_NAME.lower() or "scan" in r.TABLE_NAME.lower() or "attach" in r.TABLE_NAME.lower():
        print(f"  CANDIDATE: dbo.{r.TABLE_NAME}.{r.COLUMN_NAME}")
        # Row count
        try:
            cur.execute(f"SELECT SUM(p.rows) FROM sys.partitions p JOIN sys.tables tt ON tt.object_id=p.object_id WHERE tt.name = ? AND p.index_id IN (0,1)", (r.TABLE_NAME,))
            n = cur.fetchone()[0] or 0
            # Also check max size
            cur.execute(f"SELECT TOP 5 DATALENGTH([{r.COLUMN_NAME}]) AS sz FROM dbo.[{r.TABLE_NAME}] ORDER BY DATALENGTH([{r.COLUMN_NAME}]) DESC")
            sizes = [row.sz for row in cur.fetchall()]
            print(f"    rows={n:,}  largest DATALENGTH(s)={sizes}")
        except Exception as e:
            print(f"    (couldn't probe: {e})")
