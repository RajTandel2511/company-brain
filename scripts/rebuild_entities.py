"""Re-run entity extraction against already-extracted text.

Applies the current `entities_from_text` rules to every row in `file_content`,
replacing `file_entities` — no need to re-parse PDFs. Use after changing the
matcher to scrub out false positives like "2026" matching every year-dated file.
"""
import os, sys, sqlite3, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.chdir(Path(__file__).resolve().parents[1])

from dotenv import load_dotenv
load_dotenv(".env")

from app import docintel

t0 = time.time()
masters = docintel._load_masters()
print(f"Masters loaded: {len(masters['jobs'])} jobs, {len(masters['vendors'])} vendors, "
      f"{len(masters['customers'])} customers, {len(masters['pos'])} POs, "
      f"{len(masters.get('ap_strong', []))} strong + {len(masters.get('ap_weak', []))} weak invoices")

c = sqlite3.connect(docintel.DB, timeout=60)
c.execute("PRAGMA busy_timeout=60000")

before = c.execute("SELECT COUNT(*) FROM file_entities").fetchone()[0]
before_by_type = dict(c.execute(
    "SELECT entity_type, COUNT(*) FROM file_entities GROUP BY entity_type"
).fetchall())
print(f"Before: {before:,} entities {before_by_type}")

print("Clearing file_entities and rebuilding...")
c.execute("DELETE FROM file_entities")
c.commit()

processed = 0
ents_written = 0
cur = c.cursor()
cur.execute("BEGIN")
for file_id, text in c.execute("SELECT file_id, text FROM file_content WHERE text IS NOT NULL"):
    ents = docintel.entities_from_text(text, masters)
    for etype, eval, src in ents:
        cur.execute(
            "INSERT OR IGNORE INTO file_entities(file_id,entity_type,entity_value,source) VALUES (?,?,?,?)",
            (file_id, etype, eval, src),
        )
        ents_written += 1
    processed += 1
    if processed % 500 == 0:
        cur.execute("COMMIT"); cur.execute("BEGIN")
        print(f"  {processed:,} files processed ({ents_written:,} entities)", flush=True)
cur.execute("COMMIT")

after = c.execute("SELECT COUNT(*) FROM file_entities").fetchone()[0]
after_by_type = dict(c.execute(
    "SELECT entity_type, COUNT(*) FROM file_entities GROUP BY entity_type"
).fetchall())
print(f"\nAfter:  {after:,} entities {after_by_type}")
print(f"Processed {processed:,} files in {time.time()-t0:.1f}s")
c.close()
