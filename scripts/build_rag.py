"""Chunk + embed extracted document text into the RAG index.

Incremental: only touches files that have file_content but no chunks yet.
Runs until caught up, then sleeps 120s so newly-extracted files get indexed
without a restart.

Run with:
    python scripts/build_rag.py
"""
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
# Dev has backend/app/, Docker has app/ at the root; probe both.
for _cand in (ROOT / "backend", ROOT):
    if (_cand / "app").is_dir():
        sys.path.insert(0, str(_cand))
        break

from dotenv import load_dotenv
load_dotenv(".env")

from app import rag

BATCH_FILES = 64       # how many files to plan per iteration
IDLE_SLEEP = 120       # seconds between passes when caught up

print(f"RAG indexer starting — model={rag.MODEL_NAME}, dim={rag.EMBED_DIM}", flush=True)

# Warm the model up once so the first batch isn't misleadingly slow
t0 = time.time()
rag.embed(["warmup"])
print(f"  model loaded in {time.time() - t0:.1f}s", flush=True)

while True:
    s = rag.stats()
    print(f"[{time.strftime('%H:%M:%S')}] indexed={s['files_indexed']:,} "
          f"chunks={s['chunks']:,} pending={s['files_pending']:,}", flush=True)

    ids = rag.pending_file_ids(limit=BATCH_FILES)
    if not ids:
        print(f"  caught up — sleeping {IDLE_SLEEP}s", flush=True)
        time.sleep(IDLE_SLEEP)
        continue

    t0 = time.time()
    r = rag.index_files(ids)
    elapsed = time.time() - t0
    rate = r["chunks_written"] / elapsed if elapsed else 0
    print(f"  batch: {r['files_processed']} files, {r['chunks_written']} chunks, "
          f"{r['skipped_empty']} empty, {elapsed:.1f}s ({rate:.1f} chunks/s)", flush=True)
