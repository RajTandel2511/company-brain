"""Persistent document intelligence extractor.

Runs batches continuously until all pending PDFs are processed, then sleeps
and re-checks so newly-added files get picked up without restart. On each
idle cycle we also do an *incremental* NAS walk so freshly-dropped files
enter the pipeline without needing a manual reindex.

Run with:
    python scripts/extract_worker.py
"""
import os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.chdir(Path(__file__).resolve().parents[1])

from dotenv import load_dotenv
load_dotenv(".env")

from app import docintel, nas_index

BATCH = 200
WORKERS = 8                  # sweet spot — more threads saturate SMB and hurt throughput
IDLE_SLEEP = 120             # seconds to wait when no work is pending
REFRESH_EVERY_SECONDS = 6 * 3600  # incremental NAS walk cadence (6h)

print("Document intelligence worker starting…", flush=True)
last_refresh = 0.0

while True:
    # Catch newly-arrived NAS files periodically. Cheap compared to a full
    # rebuild because unchanged paths are an INSERT OR IGNORE no-op.
    now = time.time()
    if now - last_refresh > REFRESH_EVERY_SECONDS:
        print(f"[{time.strftime('%H:%M:%S')}] refreshing NAS index (incremental)…", flush=True)
        try:
            r = nas_index.refresh_incremental()
            print(f"  seen={r['files_seen']:,} added={r['files_added']:,} "
                  f"tokens+={r['tokens_added']:,} skipped={r['skipped']} "
                  f"in {r['elapsed_seconds']}s", flush=True)
        except Exception as e:
            print(f"  refresh failed: {e}", flush=True)
        last_refresh = time.time()

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
