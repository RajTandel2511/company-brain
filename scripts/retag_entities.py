"""Re-tag entities on already-extracted files.

Post-handoff helper: the GCP burst extractor ran with SKIP_SPECTRUM=1, so
those files have text content but no entity tags. This script reads the
existing file_content rows, loads current masters from Spectrum, and
writes file_entities rows — no PDF re-parsing needed.

Run this ONCE on the Synology after rsyncing the GCP data back.

Usage:
    python scripts/retag_entities.py           # re-tag files missing entities
    python scripts/retag_entities.py --all     # re-tag every file regardless
"""
import argparse
import os
import sys
import time
from pathlib import Path

# Dev has backend/app/, Docker has app/ at the root; probe both.
ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
for _cand in (ROOT / "backend", ROOT):
    if (_cand / "app").is_dir():
        sys.path.insert(0, str(_cand))
        break

from dotenv import load_dotenv
load_dotenv(".env")

from app import docintel


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true",
                    help="Re-tag every file, not just files missing entities.")
    ap.add_argument("--batch", type=int, default=500,
                    help="Commit every N files (default 500).")
    args = ap.parse_args()

    # SKIP_SPECTRUM must be OFF for retag to work — we need masters.
    if os.environ.get("SKIP_SPECTRUM") == "1":
        print("SKIP_SPECTRUM=1 is set. Unset it before running retag.",
              file=sys.stderr)
        sys.exit(1)

    print("Loading masters from Spectrum…", flush=True)
    t0 = time.time()
    masters = docintel._load_masters()
    print(f"  jobs: {len(masters['jobs']):,}  vendors: {len(masters['vendors']):,}  "
          f"customers: {len(masters['customers']):,}  "
          f"pos: {len(masters['pos']):,}  ap: {len(masters['ap_invoices']):,} "
          f"in {time.time() - t0:.1f}s", flush=True)

    c = docintel._connect()
    if args.all:
        q = "SELECT fc.file_id, fc.text FROM file_content fc WHERE fc.text IS NOT NULL"
    else:
        # Only files that have text but no entity rows yet
        q = """
            SELECT fc.file_id, fc.text
            FROM file_content fc
            LEFT JOIN file_entities fe ON fe.file_id = fc.file_id
            WHERE fc.text IS NOT NULL AND fe.file_id IS NULL
        """
    rows = c.execute(q).fetchall()
    print(f"Processing {len(rows):,} files…", flush=True)

    cur = c.cursor()
    cur.execute("BEGIN")
    processed = 0
    entity_count = 0
    for file_id, text in rows:
        ents = docintel.entities_from_text(text or "", masters)
        cur.execute("DELETE FROM file_entities WHERE file_id = ?", (file_id,))
        for etype, eval_, src in ents:
            cur.execute(
                "INSERT OR IGNORE INTO file_entities(file_id,entity_type,entity_value,source) "
                "VALUES (?,?,?,?)",
                (file_id, etype, eval_, src),
            )
            entity_count += 1
        processed += 1
        if processed % args.batch == 0:
            cur.execute("COMMIT")
            cur.execute("BEGIN")
            print(f"  {processed:,}/{len(rows):,} files, {entity_count:,} entities "
                  f"({time.time() - t0:.0f}s elapsed)", flush=True)

    cur.execute("COMMIT")
    c.close()
    print(f"Done. {processed:,} files retagged, {entity_count:,} entities written in "
          f"{time.time() - t0:.1f}s.", flush=True)


if __name__ == "__main__":
    main()
