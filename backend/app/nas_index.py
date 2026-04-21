"""Full-tree NAS indexer.

Walks the NAS once, tokenizes every file path, and stores an inverted index
in SQLite. Enables cross-system queries: "all files that mention job 19.50",
"all files referencing vendor CAPONE", etc.

Tokens extracted from filenames + containing directory names:
- job        : e.g. '19.50', '25.38'
- vendor     : uppercase code matching a row in VN_VENDOR_MASTER_MC
- customer   : uppercase code matching CR_CUSTOMER_MASTER_MC
- keyword    : normalized tokens for fuzzy text search

We re-read vendor/customer codes from Spectrum at index time so the match set
is current. Index is persisted in the OS temp dir as a sqlite file and
rebuilt on POST /api/files/reindex.
"""
from __future__ import annotations

import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Iterable

from .config import settings
from .db import run_query

# Persistent data dir lives at the project root so the index survives reboots
# and container restarts. In Synology deploy this gets mapped to a volume.
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB = DATA_DIR / "nas-index.sqlite"

JOB_PAT    = re.compile(r"(?<!\d)(\d{1,2}\.\d{2,3})(?!\d)")
INVOICE_PAT = re.compile(r"(?<![A-Z0-9])(\d{4,8})(?![A-Z0-9])")

SKIP_DIR_NAMES = {".AppleDB", ".AppleDouble", ".TemporaryItems",
                  "#recycle", "@eaDir", ".DS_Store", "Thumbs.db"}
SKIP_EXT = {".ds_store", ".tmp", ".bak", ".lnk"}

MAX_FILES = 500_000  # safety cap


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA synchronous=NORMAL")
    return c


def _schema(c: sqlite3.Connection) -> None:
    c.executescript("""
        CREATE TABLE IF NOT EXISTS files (
          id INTEGER PRIMARY KEY,
          path TEXT UNIQUE NOT NULL,
          name TEXT NOT NULL,
          is_dir INTEGER NOT NULL,
          size INTEGER,
          modified REAL
        );
        CREATE TABLE IF NOT EXISTS tokens (
          token_type TEXT NOT NULL,
          token_value TEXT NOT NULL,
          file_id INTEGER NOT NULL,
          PRIMARY KEY (token_type, token_value, file_id)
        ) WITHOUT ROWID;
        CREATE INDEX IF NOT EXISTS tokens_lookup
          ON tokens(token_type, token_value);
        CREATE TABLE IF NOT EXISTS meta (
          k TEXT PRIMARY KEY, v TEXT
        );
        -- Document intelligence tables live in the same DB so we can JOIN
        CREATE TABLE IF NOT EXISTS file_content (
          file_id INTEGER PRIMARY KEY,
          text TEXT,
          char_count INTEGER,
          extracted_at REAL,
          extractor TEXT
        );
        CREATE TABLE IF NOT EXISTS file_entities (
          file_id INTEGER NOT NULL,
          entity_type TEXT NOT NULL,
          entity_value TEXT NOT NULL,
          source TEXT,
          PRIMARY KEY (file_id, entity_type, entity_value)
        ) WITHOUT ROWID;
        CREATE INDEX IF NOT EXISTS file_entities_lookup
          ON file_entities(entity_type, entity_value);
    """)


def _load_spectrum_codes() -> tuple[set[str], set[str]]:
    """Pull vendor + customer codes so we can recognize them in filenames."""
    vendors: set[str] = set()
    customers: set[str] = set()
    try:
        for r in run_query(
            f"SELECT LTRIM(RTRIM(Vendor_Code)) AS v FROM dbo.VN_VENDOR_MASTER_MC "
            f"WHERE Company_Code = '{settings.spectrum_company_code}'"
        )["rows"]:
            code = (r.get("v") or "").strip().upper()
            if len(code) >= 3:
                vendors.add(code)
    except Exception:
        pass
    try:
        for r in run_query(
            f"SELECT LTRIM(RTRIM(Customer_Code)) AS c FROM dbo.CR_CUSTOMER_MASTER_MC "
            f"WHERE Company_Code = '{settings.spectrum_company_code}'"
        )["rows"]:
            code = (r.get("c") or "").strip().upper()
            if len(code) >= 3:
                customers.add(code)
    except Exception:
        pass
    return vendors, customers


def _tokens_for(name: str, path: str, vendors: set[str], customers: set[str]) -> list[tuple[str, str]]:
    tokens: set[tuple[str, str]] = set()

    # Job numbers can appear anywhere in the path
    for m in JOB_PAT.finditer(path):
        tokens.add(("job", m.group(1)))

    # Vendor / customer codes — scan uppercase tokens in path
    # split on non-alphanumeric
    upper_tokens = {t for t in re.split(r"[^A-Z0-9]+", path.upper()) if 3 <= len(t) <= 10}
    for t in upper_tokens:
        if t in vendors:
            tokens.add(("vendor", t))
        if t in customers:
            tokens.add(("customer", t))

    # Invoice-ish digit runs in the filename itself (not whole path — too noisy)
    for m in INVOICE_PAT.finditer(name):
        v = m.group(1)
        # Skip obvious year/date fragments
        if 1900 <= int(v) <= 2100:
            continue
        tokens.add(("invoice", v))

    # Light keyword tokens from filename (for fuzzy search)
    for w in re.findall(r"[A-Za-z]{4,}", name):
        tokens.add(("keyword", w.lower()))

    return list(tokens)


def _walk(root: Path) -> Iterable[Path]:
    # followlinks=True so Windows symlinks (C:\nas\X -> \\server\X) are crossed.
    # onerror swallows transient SMB failures so a flaky folder can't abort the walk.
    def _on_error(err: OSError) -> None:
        # Silently skip; total skipped count is surfaced at the end.
        return
    for dirpath, dirnames, filenames in os.walk(root, followlinks=True, onerror=_on_error):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES and not d.startswith("@")]
        p = Path(dirpath)
        yield p
        for f in filenames:
            if f in SKIP_DIR_NAMES or Path(f).suffix.lower() in SKIP_EXT:
                continue
            yield p / f


def rebuild() -> dict:
    start = time.time()
    vendors, customers = _load_spectrum_codes()
    DB.unlink(missing_ok=True)
    c = _conn()
    _schema(c)

    root = Path(settings.nas_root)
    count = 0
    tokens_count = 0

    cur = c.cursor()
    cur.execute("BEGIN")
    skipped = 0
    t_last_log = time.time()
    for entry in _walk(root):
        try:
            rel = str(entry.relative_to(root)).replace("\\", "/")
        except ValueError:
            continue
        if not rel or rel == ".":
            continue
        # Any of is_dir()/stat() can raise on SMB network blips. Skip and continue.
        try:
            is_dir = entry.is_dir()
            st = entry.stat()
        except OSError:
            skipped += 1
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
            for ttype, tval in _tokens_for(entry.name, rel, vendors, customers):
                cur.execute(
                    "INSERT OR IGNORE INTO tokens(token_type,token_value,file_id) VALUES (?,?,?)",
                    (ttype, tval, file_id),
                )
                tokens_count += 1
        except sqlite3.Error:
            skipped += 1
            continue
        count += 1
        if count % 10_000 == 0:
            cur.execute("COMMIT")
            cur.execute("BEGIN")
            elapsed = time.time() - start
            rate = count / elapsed if elapsed else 0
            print(f"  indexed {count:,} files ({tokens_count:,} tokens, {skipped} skipped) "
                  f"in {elapsed:.0f}s — {rate:.0f}/s", flush=True)
            t_last_log = time.time()
        if count >= MAX_FILES:
            break
    cur.execute("REPLACE INTO meta(k,v) VALUES ('last_build', ?)",
                (str(int(time.time())),))
    cur.execute("COMMIT")
    c.close()

    return {
        "files_indexed": count,
        "tokens_written": tokens_count,
        "skipped": skipped,
        "vendors_known": len(vendors),
        "customers_known": len(customers),
        "elapsed_seconds": round(time.time() - start, 1),
        "db_path": str(DB),
    }


def refresh_incremental(seen_ceiling: int = 0) -> dict:
    """Walk the NAS and add any paths we haven't seen before, without
    wiping the existing index. Cheap enough to run on a schedule: SMB
    stat() calls dominate runtime, but INSERT OR IGNORE makes the DB
    side a no-op for unchanged paths.

    `seen_ceiling` is a safety cap on the total NAS size (defaults to
    MAX_FILES from the full rebuild). Set higher explicitly if you've
    outgrown it."""
    start = time.time()
    vendors, customers = _load_spectrum_codes()
    c = _conn()
    _schema(c)

    root = Path(settings.nas_root)
    cap = seen_ceiling or MAX_FILES
    seen = 0
    added = 0
    tokens_added = 0
    skipped = 0
    cur = c.cursor()
    cur.execute("BEGIN")
    for entry in _walk(root):
        try:
            rel = str(entry.relative_to(root)).replace("\\", "/")
        except ValueError:
            continue
        if not rel or rel == ".":
            continue
        try:
            is_dir = entry.is_dir()
            st = entry.stat()
        except OSError:
            skipped += 1
            continue
        try:
            # Fast path: was the row already there? If so, skip the insert
            # *and* the token recomputation — those are the expensive bits.
            existing = cur.execute(
                "SELECT id FROM files WHERE path = ?", (rel,)
            ).fetchone()
            if existing is None:
                cur.execute(
                    "INSERT OR IGNORE INTO files(path,name,is_dir,size,modified) "
                    "VALUES (?,?,?,?,?)",
                    (rel, entry.name, 1 if is_dir else 0,
                     None if is_dir else st.st_size, st.st_mtime),
                )
                row = cur.execute("SELECT id FROM files WHERE path = ?",
                                  (rel,)).fetchone()
                if row:
                    file_id = row[0]
                    for ttype, tval in _tokens_for(entry.name, rel, vendors, customers):
                        cur.execute(
                            "INSERT OR IGNORE INTO tokens(token_type,token_value,file_id) "
                            "VALUES (?,?,?)",
                            (ttype, tval, file_id),
                        )
                        tokens_added += 1
                    added += 1
        except sqlite3.Error:
            skipped += 1
            continue
        seen += 1
        if seen % 20_000 == 0:
            cur.execute("COMMIT")
            cur.execute("BEGIN")
        if seen >= cap:
            break
    cur.execute(
        "REPLACE INTO meta(k,v) VALUES ('last_refresh', ?)",
        (str(int(time.time())),),
    )
    cur.execute("COMMIT")
    c.close()
    return {
        "files_seen": seen,
        "files_added": added,
        "tokens_added": tokens_added,
        "skipped": skipped,
        "elapsed_seconds": round(time.time() - start, 1),
    }


def ensure_built() -> None:
    if not DB.exists():
        rebuild()


def stats() -> dict:
    if not DB.exists():
        return {"built": False}
    c = _conn()
    _schema(c)
    n_files = c.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    n_tokens = c.execute("SELECT COUNT(*) FROM tokens").fetchone()[0]
    by_type = dict(c.execute("SELECT token_type, COUNT(*) FROM tokens GROUP BY token_type").fetchall())
    last = c.execute("SELECT v FROM meta WHERE k='last_build'").fetchone()
    c.close()
    return {
        "built": True,
        "files": n_files,
        "tokens": n_tokens,
        "by_type": by_type,
        "last_build": int(last[0]) if last else None,
    }


def find_related(token_type: str, token_value: str, limit: int = 200) -> list[dict]:
    ensure_built()
    c = _conn()
    rows = c.execute(
        """
        SELECT f.path, f.name, f.is_dir, f.size, f.modified
        FROM tokens t JOIN files f ON f.id = t.file_id
        WHERE t.token_type = ? AND t.token_value = ?
        ORDER BY f.modified DESC
        LIMIT ?
        """,
        (token_type, token_value.strip(), limit),
    ).fetchall()
    c.close()
    return [
        {"path": r[0], "name": r[1], "is_dir": bool(r[2]), "size": r[3], "modified": r[4]}
        for r in rows
    ]


def search_keyword(q: str, limit: int = 100) -> list[dict]:
    ensure_built()
    c = _conn()
    rows = c.execute(
        """
        SELECT DISTINCT f.path, f.name, f.is_dir, f.size, f.modified
        FROM tokens t JOIN files f ON f.id = t.file_id
        WHERE t.token_type = 'keyword' AND t.token_value LIKE ?
        ORDER BY f.modified DESC
        LIMIT ?
        """,
        (f"%{q.lower()}%", limit),
    ).fetchall()
    c.close()
    return [
        {"path": r[0], "name": r[1], "is_dir": bool(r[2]), "size": r[3], "modified": r[4]}
        for r in rows
    ]
