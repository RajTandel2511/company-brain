"""One-share dry run for the Synology deploy.

Indexes + extracts just a SINGLE small NAS share to prove the containers, mounts,
SQL connectivity, and OCR all work — BEFORE letting the full worker loose.

Usage inside the container:
    python scripts/dry_run.py [share_name]

Default share is `Current_Bids` (small, self-contained). To switch:
    python scripts/dry_run.py Forms
"""
import os, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.chdir(Path(__file__).resolve().parents[1])

from dotenv import load_dotenv
load_dotenv(".env")

SHARE = sys.argv[1] if len(sys.argv) > 1 else "Current_Bids"
NAS_ROOT = os.environ.get("NAS_ROOT", "/mnt/nas")
share_path = Path(NAS_ROOT) / SHARE

print(f"=== Dry run against single share: {share_path} ===\n")
if not share_path.exists():
    sys.exit(f"FAIL: {share_path} not found. Check volume mounts in docker-compose.")

# Override NAS_ROOT so the indexer only walks this share
os.environ["NAS_ROOT"] = str(share_path.parent)

from app import nas_index, docintel  # noqa: E402

print("Step 1: Build NAS index for this share…")
t0 = time.time()
r = nas_index.rebuild()
print(f"  files_indexed={r['files_indexed']}  tokens={r['tokens_written']}  skipped={r['skipped']}  {r['elapsed_seconds']}s")

print("\nStep 2: Extract + link first 50 files…")
r = docintel.run(batch_limit=50, workers=4)
print(f"  processed={r['processed']}  entities={r['entities_extracted']}  failed={r['failed']}  {r['elapsed_seconds']}s")

print("\nStep 3: Final stats")
s = docintel.stats()
print(f"  extracted={s['files_extracted']}  entities={s['entities_indexed']}  by_type={s['by_entity_type']}")
print(f"  by_extractor={s['by_extractor']}")

print(f"\nTotal wall time: {time.time()-t0:.1f}s")
print("\nIf you got here, containers + mounts + SQL + OCR all work.  Ready for full worker.")
