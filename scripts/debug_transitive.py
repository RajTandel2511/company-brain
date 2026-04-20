"""Why doesn't the transitive linking find PO/invoice files for job 19.50?"""
import os, sys, sqlite3
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.chdir(Path(__file__).resolve().parents[1])
from dotenv import load_dotenv; load_dotenv(".env")

from app import docintel
from app.db import run_query

CO = "AA1"
job = "19.50"

print("=== POs for job 19.50 ===")
po_rows = run_query(
    "SELECT LTRIM(RTRIM(PO_Number)) AS PO_Number FROM dbo.PO_PURCHASE_ORDER_HEADER_MC "
    "WHERE Company_Code = ? AND LTRIM(RTRIM(Job_Number)) = ?",
    (CO, job),
)["rows"]
print(f"  Found {len(po_rows)} POs in Spectrum")
for r in po_rows[:5]: print(f"    {r['PO_Number']!r}")

print("\n=== AP invoices for job 19.50 (distinct) ===")
inv_rows = run_query(
    "SELECT DISTINCT TOP 20 LTRIM(RTRIM(Invoice_Number)) AS Invoice_Number "
    "FROM dbo.VN_GL_DISTRIBUTION_DETAIL_MC WHERE Company_Code=? AND LTRIM(RTRIM(Job_Number))=?",
    (CO, job),
)["rows"]
print(f"  Found {len(inv_rows)} distinct invoices")
for r in inv_rows[:10]: print(f"    {r['Invoice_Number']!r}")

print("\n=== Do docintel entities exist for these? ===")
c = sqlite3.connect("data/docintel.sqlite")
for po in [r["PO_Number"] for r in po_rows[:5]]:
    n = c.execute("SELECT COUNT(*) FROM file_entities WHERE entity_type='po' AND entity_value=?", (po,)).fetchone()[0]
    print(f"  po={po!r:<12} -> {n} files")
for inv in [r["Invoice_Number"] for r in inv_rows[:10]]:
    n = c.execute("SELECT COUNT(*) FROM file_entities WHERE entity_type='ap_invoice' AND entity_value=?", (inv,)).fetchone()[0]
    print(f"  inv={inv!r:<20} -> {n} files")

print("\n=== Sample POs with files linked (any job) ===")
for po, n in c.execute("SELECT entity_value, COUNT(*) FROM file_entities WHERE entity_type='po' GROUP BY entity_value ORDER BY 2 DESC LIMIT 5"):
    print(f"  po={po!r:<12} -> {n} files")
c.close()
