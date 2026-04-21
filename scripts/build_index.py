"""Run the NAS indexer directly so we can see what it does."""
import os, sys, time
from pathlib import Path
_root = Path(__file__).resolve().parents[1]
for _cand in (_root / "backend", _root):
    if (_cand / "app").is_dir():
        sys.path.insert(0, str(_cand))
        break
os.chdir(_root)

from dotenv import load_dotenv
load_dotenv(".env")

# Pre-count quickly
root = Path(os.environ.get("NAS_ROOT", "C:/nas"))
print(f"Root: {root}")
print("Counting files (quick estimate)…")
t0 = time.time()
count = 0
dirs = 0
for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
    dirs += 1
    count += len(filenames)
    if count > 300_000:
        print(f"  …over 300K files, stopping estimate at {count} in {dirs} dirs")
        break
print(f"  Total files: ~{count} across {dirs} directories in {time.time()-t0:.1f}s")

print("\nBuilding index…")
from app import nas_index
r = nas_index.rebuild()
print(r)
