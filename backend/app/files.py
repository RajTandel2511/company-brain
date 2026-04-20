"""Synology NAS file access — read-only.

All paths are resolved relative to NAS_ROOT and bounded to it. Never follow
symlinks outside the root. Listing, searching, and streaming are supported.
"""
from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Iterator

from .config import settings

# Don't call .resolve() — that follows symlinks/junctions (the Windows dev setup
# uses C:\nas with junctions into mapped SMB drives). We rely on os.path.normpath
# + relative_to for containment instead.
ROOT = Path(os.path.normpath(settings.nas_root))


def _safe(sub: str) -> Path:
    """Resolve a user-provided path inside the NAS root, without following symlinks."""
    candidate = Path(os.path.normpath(str(ROOT / sub.lstrip("/\\"))))
    try:
        candidate.relative_to(ROOT)
    except ValueError:
        raise PermissionError("Path escapes NAS root.")
    return candidate


def list_dir(sub: str = "") -> list[dict]:
    p = _safe(sub)
    if not p.exists() or not p.is_dir():
        return []
    out = []
    for entry in sorted(p.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
        try:
            stat = entry.stat()
        except OSError:
            continue
        out.append({
            "name": entry.name,
            "path": str(entry.relative_to(ROOT)).replace("\\", "/"),
            "is_dir": entry.is_dir(),
            "size": stat.st_size if entry.is_file() else None,
            "modified": stat.st_mtime,
            "mime": mimetypes.guess_type(entry.name)[0] if entry.is_file() else None,
        })
    return out


def search(query: str, limit: int = 200) -> list[dict]:
    q = query.lower().strip()
    if not q:
        return []
    results: list[dict] = []
    for dirpath, dirnames, filenames in os.walk(ROOT, followlinks=False):
        for name in filenames + dirnames:
            if q in name.lower():
                full = Path(dirpath) / name
                try:
                    rel = full.relative_to(ROOT)
                except ValueError:
                    continue
                results.append({
                    "name": name,
                    "path": str(rel).replace("\\", "/"),
                    "is_dir": full.is_dir(),
                })
                if len(results) >= limit:
                    return results
    return results


import re
from functools import lru_cache

_JOB_PREFIX = re.compile(r"^\s*(\d{1,2}\.\d{1,3})[\s\(]")


@lru_cache(maxsize=1)
def _job_index() -> dict[str, str]:
    """Scan likely job-folder roots once, map Job_Number -> relative NAS path.

    Folder naming observed: '19.50 (M) Sutter Hotel', '22.67(A)1200 Market SF'.
    We key on the leading '<num>.<num>' prefix.
    """
    index: dict[str, str] = {}
    roots_to_scan = []
    projects = ROOT / "projects"
    if projects.is_dir():
        roots_to_scan.append(projects)
        # Sub-buckets like '0.02 Completed_Projects' hold archived jobs
        for sub in projects.iterdir():
            try:
                if sub.is_dir() and "completed" in sub.name.lower():
                    roots_to_scan.append(sub)
            except OSError:
                continue

    for root in roots_to_scan:
        try:
            entries = list(root.iterdir())
        except OSError:
            continue
        for entry in entries:
            if not entry.is_dir():
                continue
            m = _JOB_PREFIX.match(entry.name)
            if not m:
                continue
            job = m.group(1)
            rel = str(entry.relative_to(ROOT)).replace("\\", "/")
            # Prefer the first (shallower) match if duplicates across archives
            index.setdefault(job, rel)
    return index


def find_job_folder(job_number: str) -> str | None:
    """Return the NAS folder path (relative to ROOT) for a Spectrum Job_Number."""
    return _job_index().get(job_number.strip())


def invalidate_job_index() -> None:
    _job_index.cache_clear()


def stream_file(sub: str, chunk: int = 64 * 1024) -> tuple[Path, Iterator[bytes]]:
    p = _safe(sub)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(sub)

    def gen() -> Iterator[bytes]:
        with p.open("rb") as f:
            while True:
                data = f.read(chunk)
                if not data:
                    break
                yield data

    return p, gen()
