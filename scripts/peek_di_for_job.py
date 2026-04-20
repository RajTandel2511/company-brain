"""Peek at DI rows linked to a specific job (and vendor) to see what we get."""
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

for sql, label in [
    ("""SELECT TOP 15 Cabinet, Drawer, Folder, Reference, Transaction_Description
        FROM dbo.DI_MASTER_MC
        WHERE Company_Code='AA1' AND Cabinet='JOB' AND Folder LIKE '%19.50%'""",
     "DI for job 19.50"),
    ("""SELECT Cabinet, COUNT(*) AS n FROM dbo.DI_MASTER_MC
        WHERE Company_Code='AA1' GROUP BY Cabinet ORDER BY n DESC""",
     "DI by Cabinet"),
    ("""SELECT TOP 10 Cabinet, Drawer, Folder, Reference, Transaction_Description
        FROM dbo.DI_MASTER_MC
        WHERE Company_Code='AA1' AND Cabinet='VENDOR' AND Drawer='AP INVOICE'""",
     "AP invoice DI sample"),
    ("""SELECT TOP 5 m.Cabinet, m.Drawer, m.Folder, m.Reference, x.Document_ID, im.Image_Filename, im.Image_Description
        FROM dbo.DI_MASTER_MC m
        JOIN dbo.DI_IMAGE_XREF x ON x.Transaction_ID = m.Transaction_ID
        JOIN dbo.DI_IMAGE_MASTER im ON im.Document_ID = x.Document_ID
        WHERE m.Company_Code='AA1' AND m.Cabinet='JOB'""",
     "DI with image filenames (jobs)"),
]:
    print(f"\n== {label} ==")
    try:
        cur.execute(sql)
        cols = [c[0] for c in cur.description]
        print(" | ".join(cols))
        for row in cur.fetchall():
            print(" | ".join(str(v)[:50] for v in row))
    except Exception as e:
        print(f"ERROR: {e}")
