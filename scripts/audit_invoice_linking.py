"""Audit the AP invoice -> NAS file linking for false positives and noise."""
import os, sys, sqlite3
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.chdir(Path(__file__).resolve().parents[1])

from dotenv import load_dotenv
load_dotenv(".env")

from app import docintel

DB = docintel.DB
c = sqlite3.connect(DB, timeout=30)
c.execute("PRAGMA busy_timeout=30000")

print("=== 1) Distribution of invoice-number shapes in the master list ===")
# load from Spectrum via docintel helper
masters = docintel._load_masters()
import collections, re
shapes = collections.Counter()
samples = collections.defaultdict(list)
numeric = alpha = short = date_like = 0
for inv in masters["ap_invoices"]:
    inv_s = inv.strip()
    if not inv_s: continue
    if len(inv_s) <= 4: short += 1
    if inv_s.isdigit(): numeric += 1
    elif re.fullmatch(r"\d{2}[./]\d{2}[./]\d{2,4}", inv_s): date_like += 1
    else: alpha += 1
    shape = ("digit" if inv_s.isdigit() else
             "date" if re.fullmatch(r"\d{2}[./]\d{2}[./]\d{2,4}", inv_s) else
             "alphanumeric")
    shapes[shape] += 1
    if len(samples[shape]) < 5:
        samples[shape].append(inv_s)
print(f"  Total invoices: {len(masters['ap_invoices'])}")
print(f"  Numeric only: {numeric}  (often collide with amounts, years)")
print(f"  Alphanumeric: {alpha}")
print(f"  Short (<=4 chars): {short}  (very collision-prone)")
print(f"  Date-like: {date_like}  (matches arbitrary dates in PDFs)")
print("  samples:", dict(samples))

print("\n=== 2) Top 10 invoice numbers by linked-file count ===")
rows = c.execute("""
    SELECT entity_value, COUNT(*) AS n
    FROM file_entities WHERE entity_type='ap_invoice'
    GROUP BY entity_value ORDER BY n DESC LIMIT 20
""").fetchall()
for inv, n in rows:
    print(f"  {inv!r:<30} -> {n} files")

print("\n=== 3) For top invoice, look at 5 linked file names to judge signal/noise ===")
if rows:
    top = rows[0][0]
    files = c.execute("""
        SELECT f.path FROM file_entities fe
        JOIN files f ON f.id=fe.file_id
        WHERE fe.entity_type='ap_invoice' AND fe.entity_value=?
        LIMIT 8
    """, (top,)).fetchall()
    for (p,) in files:
        print(f"  {p}")

print("\n=== 4) Short numeric invoices: how many files each matches? ===")
rows = c.execute("""
    SELECT entity_value, COUNT(*) AS n
    FROM file_entities
    WHERE entity_type='ap_invoice' AND length(entity_value) <= 5
    GROUP BY entity_value ORDER BY n DESC LIMIT 10
""").fetchall()
for inv, n in rows:
    print(f"  {inv!r:<10} -> {n} files")

print("\n=== 5) Date-format invoices: how many files each matches? ===")
rows = c.execute("""
    SELECT entity_value, COUNT(*) AS n
    FROM file_entities
    WHERE entity_type='ap_invoice' AND entity_value LIKE '%.%.%'
    GROUP BY entity_value ORDER BY n DESC LIMIT 10
""").fetchall()
for inv, n in rows:
    print(f"  {inv!r:<15} -> {n} files")

print("\n=== 6) Specific spot-check: invoice 2747 (POMMYR) — do linked files actually mention this invoice? ===")
files = c.execute("""
    SELECT f.path, substr(fc.text, 1, 200) AS snippet
    FROM file_entities fe
    JOIN files f ON f.id=fe.file_id
    JOIN file_content fc ON fc.file_id=fe.file_id
    WHERE fe.entity_type='ap_invoice' AND fe.entity_value='2747'
    LIMIT 5
""").fetchall()
for p, snip in files:
    # Try to find the context around "2747" in the text
    import re as _re
    m = _re.search(r"(.{60})2747(.{60})", snip or "")
    ctx = m.group(0) if m else "[2747 not in first 200 chars]"
    print(f"  {p}")
    print(f"    context: ...{ctx[:160]}...")
