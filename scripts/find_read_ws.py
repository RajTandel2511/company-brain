"""Find READ/INQUIRE-style web service names."""
import os, pyodbc
from pathlib import Path
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

cur.execute("SELECT DISTINCT LTRIM(RTRIM(Calling_Object)) AS obj FROM dbo.PA_DATA_FUNCTION_LINKS WHERE Calling_Object LIKE 'WS.%'")
names = sorted(r.obj for r in cur.fetchall())
print(f"Total distinct WS functions: {len(names)}")

verbs = {}
for n in names:
    body = n.split(".", 1)[1]
    v = body.split("_", 1)[0]
    verbs.setdefault(v, []).append(n)
print("\nVerbs used:")
for v in sorted(verbs, key=lambda k: -len(verbs[k])):
    print(f"  {v:<12} {len(verbs[v]):>4}  e.g. {verbs[v][:3]}")

print("\nRead-ish functions (GET/READ/INQ/SEND/VIEW/QUERY/LOOKUP/LIST/EXPORT):")
for n in names:
    if any(k in n for k in ("GET","READ","INQ","VIEW","QUERY","LOOKUP","SEND","LIST","EXPORT","FETCH","RETRIEVE")):
        print(f"  {n}")

print("\nAll DI-related WS functions:")
for n in names:
    if any(k in n for k in ("DI_","DOC","IMAGE","ATTACH","SCAN")):
        print(f"  {n}")
