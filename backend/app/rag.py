"""NAS RAG — chunk, embed, and semantically search extracted document text.

Pipeline:
  file_content.text  ->  chunks table (text + embedding BLOB)
  question           ->  query embedding -> cosine top-K across chunks

Storage lives alongside docintel in data/docintel.sqlite. The embedding model
runs locally via ONNX (fastembed), so no API egress — consistent with the
LAN-only constraint of this project.
"""
from __future__ import annotations

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

def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Sliding-window character chunks. Drops chunks shorter than 40 chars
    (no signal) and strips heavy whitespace runs so embeddings don't waste
    dimensions on formatting noise."""
    if not text:
        return []
    t = " ".join(text.split())
    if len(t) <= size:
        return [t] if len(t) >= 40 else []
    chunks: list[str] = []
    step = max(1, size - overlap)
    for i in range(0, len(t), step):
        piece = t[i:i + size]
        if len(piece) >= 40:
            chunks.append(piece)
        if i + size >= len(t):
            break
    return chunks


# --- storage ----------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    c = sqlite3.connect(docintel.DB, timeout=30)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=30000")
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
    """)
    return c


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
        c.executemany(
            "INSERT OR IGNORE INTO chunks(file_id, chunk_index, text, embedding) "
            "VALUES (?,?,?,?)",
            rows,
        )
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


def search(query: str, limit: int = 10) -> list[dict]:
    """Semantic top-K across all indexed chunks. Returns rows shaped like
    Citation on the frontend, with an extra `snippet` for the LLM prompt."""
    if not query.strip():
        return []
    with _cache_lock:
        _maybe_refresh_cache()
        mat: np.ndarray = _cache["matrix"]
        ids: np.ndarray = _cache["ids"]
    if mat.shape[0] == 0:
        return []

    qv = embed([query])[0]
    # BGE outputs are unit-norm; cosine == dot product.
    scores = mat @ qv
    k = min(limit, scores.shape[0])
    top_idx = np.argpartition(-scores, k - 1)[:k]
    top_idx = top_idx[np.argsort(-scores[top_idx])]
    top_ids = ids[top_idx].tolist()
    top_scores = scores[top_idx].tolist()

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
    for cid, score in zip(top_ids, top_scores):
        r = by_id.get(cid)
        if not r:
            continue
        _, file_id, chunk_index, text, path, name, size, modified = r
        out.append({
            "file_id": file_id,
            "chunk_index": chunk_index,
            "path": path,
            "name": name,
            "size": size,
            "modified": modified,
            "score": float(score),
            "snippet": text,
            "match": "semantic",
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
