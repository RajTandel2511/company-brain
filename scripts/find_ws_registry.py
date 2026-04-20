"""Search Spectrum's DB for tables listing the valid web service names."""
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

print("=== Tables containing WS / WEB_SVC / WEBSERVICE ===")
cur.execute("""
    SELECT TABLE_SCHEMA, TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'dbo'
      AND (TABLE_NAME LIKE '%WEB_SERVICE%' OR TABLE_NAME LIKE '%WEBSERVICE%'
           OR TABLE_NAME LIKE '%WEB_SVC%' OR TABLE_NAME LIKE '%SOAP%'
           OR TABLE_NAME LIKE '%INTEGRATION%' OR TABLE_NAME LIKE '%API%')
    ORDER BY TABLE_NAME
""")
for row in cur.fetchall():
    print(f"  {row.TABLE_SCHEMA}.{row.TABLE_NAME}")

print("\n=== PA_DATA_FUNCTION_LINKS sample (might contain callable function names) ===")
cur.execute("""
    SELECT TOP 30
        LTRIM(RTRIM(Calling_Object))  AS Calling_Object,
        LTRIM(RTRIM(Calling_Object_Class)) AS Calling_Class,
        LTRIM(RTRIM(Called_Object))   AS Called_Object,
        LTRIM(RTRIM(Called_Object_Class)) AS Called_Class
    FROM dbo.PA_DATA_FUNCTION_LINKS
    WHERE Called_Object LIKE 'WS_%' OR Called_Object LIKE 'API_%' OR Called_Object LIKE '%WEB%'
""")
for row in cur.fetchall():
    print(f"  {row.Calling_Object:<30} ({row.Calling_Class}) -> {row.Called_Object:<30} ({row.Called_Class})")

print("\n=== Distinct Calling_Object_Class / Called_Object_Class values ===")
cur.execute("""
    SELECT DISTINCT LTRIM(RTRIM(Called_Object_Class)) AS C
    FROM dbo.PA_DATA_FUNCTION_LINKS ORDER BY C
""")
for row in cur.fetchall():
    print(f"  {row.C!r}")

print("\n=== Candidate: objects whose class looks like 'WS' or 'SOAP' ===")
cur.execute("""
    SELECT DISTINCT TOP 50 LTRIM(RTRIM(Called_Object)) AS obj, LTRIM(RTRIM(Called_Object_Class)) AS cls
    FROM dbo.PA_DATA_FUNCTION_LINKS
    WHERE Called_Object_Class IN ('WS','WB','SP','WS1','WS2') OR Called_Object LIKE 'WS_%'
""")
for row in cur.fetchall():
    print(f"  {row.obj}  ({row.cls})")

print("\n=== Distinct Function_Type values in PA_DATA_TABLE_FUNCTION_XREF ===")
cur.execute("""
    SELECT DISTINCT TOP 30 LTRIM(RTRIM(Function_Type)) AS FT, COUNT(*) AS N
    FROM dbo.PA_DATA_TABLE_FUNCTION_XREF GROUP BY Function_Type ORDER BY N DESC
""")
for row in cur.fetchall():
    print(f"  type={row.FT!r:<10} count={row.N}")

print("\n=== Function_Title examples for type='WS' or 'SP' if any ===")
cur.execute("""
    SELECT DISTINCT TOP 30 LTRIM(RTRIM(Function_Name)) AS F, LTRIM(RTRIM(Function_Title)) AS T, LTRIM(RTRIM(Function_Type)) AS FT
    FROM dbo.PA_DATA_TABLE_FUNCTION_XREF WHERE Function_Type IN ('WS','SP','SR','WB')
""")
for row in cur.fetchall():
    print(f"  {row.F:<30} [{row.FT}]  {row.T}")

print("\n=== PA_DATA_WORKFLOWS — might contain callable workflow names ===")
cur.execute("""
    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'PA_DATA_WORKFLOWS' ORDER BY ORDINAL_POSITION
""")
for row in cur.fetchall():
    print(f"  {row.COLUMN_NAME}")
