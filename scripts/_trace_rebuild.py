"""Instrumented rebuild to trace why the indexer only sees 24 entries."""
import os, sys, time, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv
load_dotenv(".env")

from app import nas_index
from app.config import settings

print("settings.nas_root =", settings.nas_root, flush=True)
print("DB =", nas_index.DB, flush=True)

start = time.time()
print(f"[t={time.time()-start:.1f}] loading spectrum codes...", flush=True)
vendors, customers = nas_index._load_spectrum_codes()
print(f"[t={time.time()-start:.1f}] vendors={len(vendors)} customers={len(customers)}", flush=True)

print(f"[t={time.time()-start:.1f}] unlinking DB...", flush=True)
nas_index.DB.unlink(missing_ok=True)
print(f"[t={time.time()-start:.1f}] connecting...", flush=True)
c = nas_index._conn()
nas_index._schema(c)

root = Path(settings.nas_root)
count = 0
tokens_count = 0
skipped = 0
cur = c.cursor()
cur.execute("BEGIN")
print(f"[t={time.time()-start:.1f}] begin walk of {root}", flush=True)

try:
    for entry in nas_index._walk(root):
        try:
            rel = str(entry.relative_to(root)).replace("\\", "/")
        except ValueError:
            continue
        if not rel or rel == ".":
            continue
        try:
            is_dir = entry.is_dir()
            st = entry.stat()
        except OSError as e:
            skipped += 1
            if skipped <= 5:
                print(f"  SKIP OSError on {entry}: {e}", flush=True)
            continue
        try:
            cur.execute(
                "INSERT OR IGNORE INTO files(path,name,is_dir,size,modified) VALUES (?,?,?,?,?)",
                (rel, entry.name, 1 if is_dir else 0,
                 None if is_dir else st.st_size, st.st_mtime),
            )
            row = cur.execute("SELECT id FROM files WHERE path = ?", (rel,)).fetchone()
            if not row:
                continue
            file_id = row[0]
            for ttype, tval in nas_index._tokens_for(entry.name, rel, vendors, customers):
                cur.execute(
                    "INSERT OR IGNORE INTO tokens(token_type,token_value,file_id) VALUES (?,?,?)",
                    (ttype, tval, file_id),
                )
                tokens_count += 1
        except Exception as e:
            skipped += 1
            if skipped <= 10:
                print(f"  SKIP sqlerr on {entry}: {type(e).__name__}: {e}", flush=True)
            continue
        count += 1
        if count % 5000 == 0:
            cur.execute("COMMIT"); cur.execute("BEGIN")
            print(f"[t={time.time()-start:.1f}] {count:,} files, {tokens_count:,} tokens, {skipped} skipped", flush=True)
        if count >= nas_index.MAX_FILES:
            break
except BaseException as e:
    print(f"OUTER EXCEPTION: {type(e).__name__}: {e}", flush=True)
    traceback.print_exc()

cur.execute("REPLACE INTO meta(k,v) VALUES ('last_build', ?)", (str(int(time.time())),))
cur.execute("COMMIT")
c.close()
print(f"DONE: {count:,} files, {tokens_count:,} tokens, {skipped} skipped, {time.time()-start:.1f}s", flush=True)
