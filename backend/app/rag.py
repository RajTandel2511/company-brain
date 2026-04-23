"""NAS RAG — chunk, embed, and semantically search extracted document text.

Pipeline:
  file_content.text  ->  chunks table (text + embedding BLOB)
  question           ->  query embedding -> cosine top-K across chunks

Storage lives alongside docintel in data/docintel.sqlite. The embedding model
runs locally via ONNX (fastembed), so no API egress — consistent with the
LAN-only constraint of this project.
"""
from __future__ import annotations

import re
import sqlite3
import threading
from pathlib import Path
from typing import Iterable

import numpy as np

from . import docintel, nas_index

# --- model ------------------------------------------------------------------

MODEL_NAME = "BAAI/bge-small-en-v1.5"   # 384-dim, English, ~130MB ONNX
EMBED_DIM = 384
CHUNK_SIZE = 800                         # characters, not tokens
CHUNK_OVERLAP = 150

_model = None
_model_lock = threading.Lock()


def _embedder():
    """Lazy-load the ONNX model on first use. Thread-safe."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                from fastembed import TextEmbedding
                _model = TextEmbedding(model_name=MODEL_NAME)
    return _model


def embed(texts: list[str]) -> np.ndarray:
    """Return an (N, EMBED_DIM) float32 array. Already L2-normalised by BGE."""
    if not texts:
        return np.zeros((0, EMBED_DIM), dtype=np.float32)
    vecs = list(_embedder().embed(texts))
    return np.vstack(vecs).astype(np.float32, copy=False)


# --- chunking ---------------------------------------------------------------

# Separators tried in order. Earlier = stronger semantic boundary. A chunk
# longer than `size` is recursively split on the first separator that
# produces pieces small enough, then the next, and so on.
_SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " ", ""]

_MIN_CHUNK_CHARS = 40


def _split_recursive(text: str, size: int, separators: list[str]) -> list[str]:
    if len(text) <= size:
        return [text]
    if not separators:
        # Hard char-level split as a last resort.
        return [text[i:i + size] for i in range(0, len(text), size)]

    sep = separators[0]
    parts = text.split(sep) if sep else list(text)
    out: list[str] = []
    buf = ""
    glue = sep if sep else ""
    for p in parts:
        candidate = p if not buf else buf + glue + p
        if len(candidate) <= size:
            buf = candidate
            continue
        if buf:
            out.append(buf)
        if len(p) > size:
            out.extend(_split_recursive(p, size, separators[1:]))
            buf = ""
        else:
            buf = p
    if buf:
        out.append(buf)
    return out


def _merge_with_overlap(pieces: list[str], size: int, overlap: int) -> list[str]:
    """Greedy merge adjacent pieces up to `size`, with character-level tail
    overlap between neighbours so a fact straddling a boundary still lands
    wholly inside at least one chunk."""
    if not pieces:
        return []
    chunks: list[str] = []
    cur = ""
    for p in pieces:
        p = p.strip()
        if not p:
            continue
        candidate = p if not cur else cur + " " + p
        if len(candidate) <= size:
            cur = candidate
            continue
        if cur:
            chunks.append(cur)
            tail = cur[-overlap:] if overlap > 0 else ""
            cur = (tail + " " + p).strip() if tail else p
        else:
            cur = p
    if cur:
        chunks.append(cur)
    return [c for c in chunks if len(c) >= _MIN_CHUNK_CHARS]


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Recursive chunker that respects paragraph → sentence → word
    boundaries. Cleaner snippets than a raw character window and better
    embeddings because the model sees coherent units."""
    if not text:
        return []
    # Preserve paragraph breaks (they carry structure) but squash runs of
    # whitespace inside each line so extraction noise doesn't explode size.
    normalised = "\n\n".join(
        " ".join(line.split())
        for line in text.split("\n")
        if line.strip()
    )
    if len(normalised) <= size:
        return [normalised] if len(normalised) >= _MIN_CHUNK_CHARS else []
    pieces = _split_recursive(normalised, size, _SEPARATORS)
    return _merge_with_overlap(pieces, size, overlap)


# --- storage ----------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    # Ensure docintel's schema exists in the shared DB. On a fresh deploy
    # the RAG worker can start before the extractor has created
    # file_content / file_entities, and our queries need those tables.
    docintel._connect().close()

    c = sqlite3.connect(docintel.DB, timeout=120)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=120000")
    c.executescript("""
        CREATE TABLE IF NOT EXISTS chunks (
          id INTEGER PRIMARY KEY,
          file_id INTEGER NOT NULL,
          chunk_index INTEGER NOT NULL,
          text TEXT NOT NULL,
          embedding BLOB NOT NULL,
          UNIQUE(file_id, chunk_index)
        );
        CREATE INDEX IF NOT EXISTS chunks_file ON chunks(file_id);
        CREATE TABLE IF NOT EXISTS rag_meta (
          k TEXT PRIMARY KEY, v TEXT
        );

        -- Contentless FTS5 mirror of chunks(text). We write to it manually
        -- after each insert so the index stays in lockstep without the
        -- overhead of triggers or a full-text content table duplicate.
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
          text, content='chunks', content_rowid='id', tokenize='porter unicode61'
        );
    """)
    return c


def _fts_index(c: sqlite3.Connection, rows: list[tuple[int, str]]) -> None:
    """Push chunk (rowid, text) pairs into the FTS mirror."""
    if not rows:
        return
    c.executemany("INSERT INTO chunks_fts(rowid, text) VALUES (?,?)", rows)


def _pack(vec: np.ndarray) -> bytes:
    return vec.astype(np.float32, copy=False).tobytes()


def _unpack(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


# --- index build ------------------------------------------------------------

def pending_file_ids(limit: int | None = None) -> list[int]:
    """file_ids that have extracted text but no chunks yet."""
    c = _connect()
    q = """
        SELECT fc.file_id
        FROM file_content fc
        LEFT JOIN chunks ch ON ch.file_id = fc.file_id
        WHERE fc.text IS NOT NULL
          AND fc.char_count > 0
          AND ch.file_id IS NULL
        GROUP BY fc.file_id
    """
    if limit:
        q += f" LIMIT {int(limit)}"
    rows = c.execute(q).fetchall()
    c.close()
    return [r[0] for r in rows]


def index_files(file_ids: list[int], embed_batch: int = 64) -> dict:
    """Chunk + embed the given file_ids. Skips files that already have chunks.
    Returns {files_processed, chunks_written, skipped_empty}."""
    if not file_ids:
        return {"files_processed": 0, "chunks_written": 0, "skipped_empty": 0}

    c = _connect()
    # Pull text for all requested files in one go
    placeholders = ",".join("?" for _ in file_ids)
    rows = c.execute(
        f"SELECT file_id, text FROM file_content WHERE file_id IN ({placeholders})",
        file_ids,
    ).fetchall()
    text_by_id = {fid: (txt or "") for fid, txt in rows}

    # Chunk everything first so we can batch embeddings across files
    plan: list[tuple[int, int, str]] = []  # (file_id, chunk_index, text)
    skipped = 0
    for fid in file_ids:
        pieces = chunk_text(text_by_id.get(fid, ""))
        if not pieces:
            skipped += 1
            continue
        for i, p in enumerate(pieces):
            plan.append((fid, i, p))

    chunks_written = 0
    for start in range(0, len(plan), embed_batch):
        batch = plan[start:start + embed_batch]
        vecs = embed([p[2] for p in batch])
        rows = [(fid, idx, txt, _pack(v)) for (fid, idx, txt), v in zip(batch, vecs)]
        cur = c.executemany(
            "INSERT OR IGNORE INTO chunks(file_id, chunk_index, text, embedding) "
            "VALUES (?,?,?,?)",
            rows,
        )
        # Pull the rowids we just assigned so we can mirror into FTS.
        fts_rows: list[tuple[int, str]] = []
        for (fid, idx, txt, _blob) in rows:
            row = c.execute(
                "SELECT id FROM chunks WHERE file_id=? AND chunk_index=?",
                (fid, idx),
            ).fetchone()
            if row:
                fts_rows.append((row[0], txt))
        _fts_index(c, fts_rows)
        c.commit()
        chunks_written += len(rows)

    c.close()
    return {
        "files_processed": len(file_ids) - skipped,
        "chunks_written": chunks_written,
        "skipped_empty": skipped,
    }


# --- search -----------------------------------------------------------------

# Cache all embeddings in memory for fast cosine. Invalidate on index grow.
_cache_lock = threading.Lock()
_cache: dict[str, object] = {"count": 0, "ids": None, "matrix": None}


def _maybe_refresh_cache() -> None:
    c = _connect()
    n = c.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    if n == _cache["count"] and _cache["matrix"] is not None:
        c.close()
        return
    rows = c.execute("SELECT id, embedding FROM chunks").fetchall()
    c.close()
    if not rows:
        _cache.update({"count": 0, "ids": np.zeros(0, dtype=np.int64),
                       "matrix": np.zeros((0, EMBED_DIM), dtype=np.float32)})
        return
    ids = np.fromiter((r[0] for r in rows), dtype=np.int64, count=len(rows))
    mat = np.stack([_unpack(r[1]) for r in rows])
    _cache.update({"count": len(rows), "ids": ids, "matrix": mat})


def _dense_candidates(query: str, pool: int) -> list[tuple[int, float]]:
    """Return up to `pool` (chunk_id, cosine_score) candidates."""
    with _cache_lock:
        _maybe_refresh_cache()
        mat: np.ndarray = _cache["matrix"]
        ids: np.ndarray = _cache["ids"]
    if mat.shape[0] == 0:
        return []
    qv = embed([query])[0]
    scores = mat @ qv  # BGE vectors are unit-norm → dot == cosine
    k = min(pool, scores.shape[0])
    top_idx = np.argpartition(-scores, k - 1)[:k]
    top_idx = top_idx[np.argsort(-scores[top_idx])]
    return [(int(ids[i]), float(scores[i])) for i in top_idx]


# FTS5 MATCH is allergic to punctuation — strip everything except word chars,
# quote each remaining term, OR them together. "PO #25-0421 mechanical" ->
# '"PO" OR "25" OR "0421" OR "mechanical"'.
_FTS_TOKEN = re.compile(r"[A-Za-z0-9]{2,}")


def _fts_query(query: str) -> str:
    terms = _FTS_TOKEN.findall(query)
    if not terms:
        return ""
    return " OR ".join(f'"{t}"' for t in terms)


def _keyword_candidates(query: str, pool: int) -> list[tuple[int, float]]:
    """Return up to `pool` (chunk_id, bm25_score) candidates via FTS5."""
    q = _fts_query(query)
    if not q:
        return []
    c = _connect()
    try:
        rows = c.execute(
            "SELECT rowid, bm25(chunks_fts) AS s FROM chunks_fts "
            "WHERE chunks_fts MATCH ? ORDER BY s LIMIT ?",
            (q, pool),
        ).fetchall()
    except sqlite3.OperationalError:
        rows = []
    c.close()
    # bm25() returns a *lower-is-better* score; flip sign so higher=better for
    # the caller's convenience (fusion only cares about rank anyway).
    return [(int(r[0]), -float(r[1])) for r in rows]


def _rrf_merge(
    dense: list[tuple[int, float]],
    sparse: list[tuple[int, float]],
    k: int = 60,
) -> list[tuple[int, float]]:
    """Reciprocal Rank Fusion. k=60 is the literature default; treating both
    rankers as equally weighted works well in practice."""
    scores: dict[int, float] = {}
    for rank, (cid, _) in enumerate(dense):
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
    for rank, (cid, _) in enumerate(sparse):
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def search(query: str, limit: int = 10, pool: int = 30) -> list[dict]:
    """Hybrid top-K: dense vector + BM25 FTS, merged via RRF. Returns rows
    shaped like Citation for the frontend, with a snippet for the LLM."""
    if not query.strip():
        return []

    dense = _dense_candidates(query, pool)
    sparse = _keyword_candidates(query, pool)
    if not dense and not sparse:
        return []

    fused = _rrf_merge(dense, sparse)[:limit]
    top_ids = [cid for cid, _ in fused]
    fused_score = {cid: s for cid, s in fused}
    # Keep per-ranker signal for display / debugging.
    dense_score = {cid: s for cid, s in dense}
    sparse_score = {cid: s for cid, s in sparse}

    c = _connect()
    placeholders = ",".join("?" for _ in top_ids)
    rows = c.execute(
        f"""
        SELECT ch.id, ch.file_id, ch.chunk_index, ch.text,
               f.path, f.name, f.size, f.modified
        FROM chunks ch
        JOIN files f ON f.id = ch.file_id
        WHERE ch.id IN ({placeholders})
        """,
        top_ids,
    ).fetchall()
    c.close()

    by_id = {r[0]: r for r in rows}
    out: list[dict] = []
    for cid in top_ids:
        r = by_id.get(cid)
        if not r:
            continue
        _, file_id, chunk_index, text, path, name, size, modified = r
        d = dense_score.get(cid)
        s = sparse_score.get(cid)
        if d is not None and s is not None:
            match = "hybrid"
        elif s is not None:
            match = "keyword"
        else:
            match = "semantic"
        out.append({
            "file_id": file_id,
            "chunk_index": chunk_index,
            "path": path,
            "name": name,
            "size": size,
            "modified": modified,
            "score": float(fused_score[cid]),
            "dense_score": d,
            "bm25_score": s,
            "snippet": text,
            "match": match,
        })
    return out


# --- stats ------------------------------------------------------------------

def stats() -> dict:
    c = _connect()
    n_chunks = c.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    n_files = c.execute("SELECT COUNT(DISTINCT file_id) FROM chunks").fetchone()[0]
    n_extracted = c.execute("SELECT COUNT(*) FROM file_content").fetchone()[0]
    c.close()
    return {
        "model": MODEL_NAME,
        "dim": EMBED_DIM,
        "chunks": n_chunks,
        "files_indexed": n_files,
        "files_extracted": n_extracted,
        "files_pending": max(0, n_extracted - n_files),
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
    }
