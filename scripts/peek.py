"""Quick peek to confirm company code and a few sample values."""
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
    ("SELECT DISTINCT Company_Code FROM dbo.JC_JOB_MASTER_MC", "Company codes"),
    ("SELECT Status_Code, COUNT(*) AS n FROM dbo.JC_JOB_MASTER_MC GROUP BY Status_Code ORDER BY n DESC", "Job status codes"),
    ("SELECT TOP 3 Job_Number, Job_Description, Status_Code, Original_Contract, Start_Date, Complete_Date FROM dbo.JC_JOB_MASTER_MC WHERE Status_Code = 'O' ORDER BY Original_Contract DESC", "Top 3 biggest open jobs"),
    ("SELECT MIN(Invoice_Date), MAX(Invoice_Date), COUNT(*) FROM dbo.CR_INVOICE_HEADER_MC", "AR invoice date range"),
]:
    print(f"\n== {label} ==")
    try:
        cur.execute(sql)
        cols = [c[0] for c in cur.description]
        for row in cur.fetchall():
            print(" | ".join(f"{c}={v!r}" for c, v in zip(cols, row)))
    except Exception as e:
        print(f"ERROR: {e}")
