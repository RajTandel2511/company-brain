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

# Dev layout: backend/app/ alongside scripts/. Docker layout: app/ alongside
# scripts/ (backend/ is flattened into the image root). Probe both.
_root = Path(__file__).resolve().parents[1]
for _cand in (_root / "backend", _root):
    if (_cand / "app").is_dir():
        sys.path.insert(0, str(_cand))
        break
os.chdir(_root)

from dotenv import load_dotenv
load_dotenv(".env")

from app import docintel, nas_index

BATCH = 200
# Thread count tuned for a shared Synology box. DSM itself needs headroom
# for SMB / indexer / Drive, and the kernel here doesn't expose CFS cgroup
# limits so this is the only real CPU ceiling we have. Override with the
# EXTRACT_WORKERS env var if you want to push harder on a dedicated host.
WORKERS = int(os.environ.get("EXTRACT_WORKERS", "3"))
IDLE_SLEEP = 120             # seconds to wait when no work is pending
REFRESH_EVERY_SECONDS = int(os.environ.get("REFRESH_EVERY_SECONDS", 6 * 3600))
# When the NAS is mounted over high-latency SMB (e.g. Tailscale from a cloud
# VM), the stat()-per-file walk can take hours. Set SKIP_NAS_REFRESH=1 so
# the burst node only works through the existing index; newly-added files
# get picked up later by the Synology on its next 6h refresh.
SKIP_NAS_REFRESH = os.environ.get("SKIP_NAS_REFRESH") == "1"

print("Document intelligence worker starting…", flush=True)
if SKIP_NAS_REFRESH:
    print("  SKIP_NAS_REFRESH=1 → skipping incremental walks this run", flush=True)
last_refresh = 0.0

while True:
    # Catch newly-arrived NAS files periodically. Cheap compared to a full
    # rebuild because unchanged paths are an INSERT OR IGNORE no-op — unless
    # the mount is slow, in which case SKIP_NAS_REFRESH disables this.
    now = time.time()
    if not SKIP_NAS_REFRESH and now - last_refresh > REFRESH_EVERY_SECONDS:
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
