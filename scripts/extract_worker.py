"""Persistent document intelligence extractor.

Runs batches continuously until all pending PDFs are processed, then sleeps
and re-checks so newly-added files get picked up without restart.

Run with:
    python scripts/extract_worker.py
"""
import os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.chdir(Path(__file__).resolve().parents[1])

from dotenv import load_dotenv
load_dotenv(".env")

from app import docintel

BATCH = 200
WORKERS = 6          # threads per batch — set 4-8 based on your CPU
IDLE_SLEEP = 120     # seconds to wait when no work is pending

print("Document intelligence worker starting…", flush=True)
while True:
    s = docintel.stats()
    pending = s.get("pdfs_pending", 0)
    total = s.get("files_extracted", 0)
    ents = s.get("entities_indexed", 0)
    print(f"[{time.strftime('%H:%M:%S')}] extracted={total:,} entities={ents:,} pending={pending:,}", flush=True)

    if pending == 0:
        print(f"  caught up — sleeping {IDLE_SLEEP}s", flush=True)
        time.sleep(IDLE_SLEEP)
        continue

    r = docintel.run(batch_limit=BATCH, workers=WORKERS)
    rate = r["processed"] / r["elapsed_seconds"] if r["elapsed_seconds"] else 0
    print(f"  batch: {r['processed']} files, {r['entities_extracted']} entities, "
          f"{r['failed']} failed, {r['elapsed_seconds']}s ({rate:.1f}/s with {r['workers']} threads)", flush=True)
