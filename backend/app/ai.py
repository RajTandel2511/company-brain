"""LLM orchestration: NL → SQL → answer.

Providers:
- anthropic (default): Claude Haiku 4.5 for cost, optional bigger model on summary.
- ollama: local LLM, zero API cost.

Also: prompt caching on the schema (Anthropic only, 90% off cache reads) and a
SQLite response cache keyed on (question + schema + provider + model).
"""
from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from typing import Any

import urllib.request

from anthropic import Anthropic

from . import cache, spectrum_knowledge
from .config import settings
from .db import list_tables, run_query, UnsafeSQLError

# Column name → docintel entity_type.
# First match wins per row, but all columns get scanned.
_CITATION_COLS: list[tuple[str, str]] = [
    ("invoice_number", "ap_invoice"),
    ("invoice_or_transaction", "ap_invoice"),
    ("po_number", "po"),
    ("job_number", "job"),
    ("vendor_code", "vendor"),
    ("customer_code", "customer"),
]


def _nas_by_token(token_type: str, token_value: str, limit: int) -> list[dict]:
    """Look up files in the NAS filename index by token."""
    import sqlite3
    from . import nas_index
    try:
        c = sqlite3.connect(nas_index.DB, timeout=15)
        rows = c.execute("""
            SELECT f.id, f.path, f.name, f.size, f.modified
            FROM tokens t JOIN files f ON f.id = t.file_id
            WHERE t.token_type = ? AND t.token_value = ? AND f.is_dir = 0
            ORDER BY f.modified DESC
            LIMIT ?
        """, (token_type, token_value, limit)).fetchall()
        c.close()
    except Exception:
        return []
    return [{"file_id": r[0], "path": r[1], "name": r[2], "size": r[3],
             "modified": r[4], "match": "filename"} for r in rows]


def _nas_by_name_fuzzy(display_name: str, limit: int) -> list[dict]:
    """Find NAS files whose filename contains all distinctive words from a
    display name, separator-agnostic. E.g. 'Superior Seamless Gutter' matches
    'Inv_155798_from_Superior_Seamless_Gutter_10648.pdf'."""
    import re as _re
    import sqlite3
    from . import nas_index
    words = [w.lower() for w in _re.findall(r"[A-Za-z0-9]{4,}", display_name or "")]
    if len(words) < 2:
        return []
    pattern = "%" + "%".join(words) + "%"
    try:
        c = sqlite3.connect(nas_index.DB, timeout=15)
        rows = c.execute("""
            SELECT f.id, f.path, f.name, f.size, f.modified
            FROM files f
            WHERE f.is_dir = 0 AND LOWER(f.name) LIKE ?
            ORDER BY f.modified DESC
            LIMIT ?
        """, (pattern, limit)).fetchall()
        c.close()
    except Exception:
        return []
    return [{"file_id": r[0], "path": r[1], "name": r[2], "size": r[3],
             "modified": r[4], "match": "name"} for r in rows]


_NAME_COL_SUFFIX = ("_name", "_description")


def _display_name_from_row(row: dict, col_map: dict, entity_col_lower: str) -> str | None:
    """Given a row + the column that held the entity value, try to find a
    paired display-name column (Vendor_Code → Vendor_Name, Customer_Code →
    Customer_Name / Name, Job_Number → Job_Description)."""
    base = entity_col_lower.rsplit("_", 1)[0]  # 'vendor_code' → 'vendor'
    for suffix in _NAME_COL_SUFFIX:
        cand = col_map.get(base + suffix)
        if cand and row.get(cand):
            return str(row[cand]).strip()
    # Customer_Code rows sometimes just have a 'Name' column
    if base == "customer":
        cand = col_map.get("name")
        if cand and row.get(cand):
            return str(row[cand]).strip()
    return None


def _find_citations(result: dict[str, Any], max_per_entity: int = 3, max_total: int = 12) -> list[dict]:
    """Scan SQL result rows for identifiable entity values and look them up
    across the docintel (content) and nas_index (filename) indexes. Prefers
    content matches but falls back to filename matches so we get hits even on
    files the docintel extractor hasn't reached yet."""
    from . import docintel
    if not result or not result.get("rows"):
        return []
    columns = result.get("columns") or []
    col_map = {c.lower(): c for c in columns}

    # Collect (entity_type, value, display_name) in priority order.
    wanted: list[tuple[str, str, str | None]] = []
    seen_vals: set[tuple[str, str]] = set()
    for col_lower, etype in _CITATION_COLS:
        col = col_map.get(col_lower)
        if not col:
            continue
        for row in result["rows"]:
            v = row.get(col)
            if v is None:
                continue
            sv = str(v).strip()
            if not sv or sv.upper() in {"NULL", "NONE", "N/A"}:
                continue
            key = (etype, sv)
            if key in seen_vals:
                continue
            seen_vals.add(key)
            name = _display_name_from_row(row, col_map, col_lower)
            wanted.append((etype, sv, name))

    if not wanted:
        return []

    # NAS-index token type maps roughly 1:1 to our entity types.
    NAS_TOKEN = {"job": "job", "vendor": "vendor", "customer": "customer",
                 "ap_invoice": "invoice", "po": "invoice"}

    out: list[dict] = []
    seen_files: set[int] = set()

    def _add(hits: list[dict], etype: str, val: str, source: str) -> int:
        added = 0
        for h in hits:
            fid = h.get("file_id")
            if fid is None or fid in seen_files:
                continue
            seen_files.add(fid)
            out.append({
                "file_id": fid,
                "path": h["path"],
                "name": h["name"],
                "size": h.get("size"),
                "modified": h.get("modified"),
                "entity_type": etype,
                "entity_value": val,
                "match": source,
            })
            added += 1
            if added >= max_per_entity:
                break
        return added

    for etype, val, display in wanted:
        if len(out) >= max_total:
            break
        # 1. Docintel content match (most precise).
        try:
            _add(docintel.files_for_entity(etype, val, limit=max_per_entity * 2),
                 etype, val, "content")
        except Exception:
            pass
        if len(out) >= max_total:
            break
        # 2. NAS filename token match (works even before docintel has run).
        tok = NAS_TOKEN.get(etype)
        if tok:
            _add(_nas_by_token(tok, val, limit=max_per_entity * 2), etype, val, "filename")
        if len(out) >= max_total:
            break
        # 3. Vendor/customer: fuzzy match on display name (most filenames use
        #    the human-readable name rather than the code).
        if display and etype in ("vendor", "customer"):
            _add(_nas_by_name_fuzzy(display, limit=max_per_entity * 2), etype, val, "name")

    return out[:max_total]


def _system_prompt() -> str:
    return (
        "You are the analytics brain for a construction company running on Trimble "
        "Spectrum by Viewpoint (Microsoft SQL Server).\n\n"
        "You have READ-ONLY access. Only emit a single SELECT (or WITH ... SELECT) statement.\n"
        "- Use SQL Server T-SQL syntax.\n"
        "- Always include TOP N (default 200) unless the user asks for a specific count or aggregate.\n"
        "- Prefer the tables listed below. If the user's question is ambiguous, pick the most likely interpretation and proceed.\n"
        "- Use JOINs conservatively; avoid SELECT *.\n\n"
        + spectrum_knowledge.render(settings.spectrum_company_code)
        + "\nOutput format — always emit exactly this XML structure:\n"
        "<reasoning>one short sentence on the plan</reasoning>\n"
        "<sql>the single SELECT statement, no trailing semicolon</sql>\n"
    )


SYSTEM_PROMPT = _system_prompt()


@lru_cache(maxsize=1)
def _schema_snapshot() -> str:
    """Filter the 6,000+ Spectrum objects down to business-relevant _MC tables."""
    tables = list_tables()
    # Keep only _MC business tables (multi-company) and drop noise.
    NOISE = ("TEMP", "WORK", "PA_", "MS", "Z_", "BI_", "CL_", "CP_", "ET_")
    kept = []
    for t in tables:
        name = t["table_name"]
        if not name.endswith("_MC") and not name.endswith("_MC_ID"):
            continue
        if any(name.startswith(p) for p in NOISE) or "TEMP" in name or "_WORK_" in name:
            continue
        if t["schema_name"] != "dbo":
            continue
        kept.append(f"dbo.{name}")
    return "Available business tables (multi-company):\n" + "\n".join(sorted(kept))


def _schema_hash() -> str:
    return hashlib.sha256(_schema_snapshot().encode()).hexdigest()[:16]


def _parse(text: str) -> tuple[str, str]:
    reasoning = re.search(r"<reasoning>(.*?)</reasoning>", text, re.DOTALL)
    sql = re.search(r"<sql>(.*?)</sql>", text, re.DOTALL)
    if not sql:
        # Fallback: models sometimes emit a bare ```sql fenced block
        fenced = re.search(r"```sql\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if not fenced:
            raise ValueError("Model did not emit SQL.")
        return ("", fenced.group(1).strip().rstrip(";"))
    return (reasoning.group(1).strip() if reasoning else "", sql.group(1).strip().rstrip(";"))


# ---- Anthropic -----------------------------------------------------------

_anthropic: Anthropic | None = None


def _get_anthropic() -> Anthropic:
    global _anthropic
    if _anthropic is None:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set.")
        _anthropic = Anthropic(api_key=settings.anthropic_api_key)
    return _anthropic


def _anthropic_nl_to_sql(question: str) -> dict[str, Any]:
    system_blocks = [
        {"type": "text", "text": SYSTEM_PROMPT},
        {
            "type": "text",
            "text": _schema_snapshot(),
            "cache_control": {"type": "ephemeral"},
        },
    ]
    resp = _get_anthropic().messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        system=system_blocks,
        messages=[{"role": "user", "content": question}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    reasoning, sql = _parse(text)
    return {
        "reasoning": reasoning,
        "sql": sql,
        "model": settings.anthropic_model,
        "usage": resp.usage.model_dump() if resp.usage else {},
    }


def _anthropic_summarize(prompt: str) -> str:
    model = settings.anthropic_summary_model or settings.anthropic_model
    resp = _get_anthropic().messages.create(
        model=model,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


# ---- Ollama --------------------------------------------------------------

def _ollama_chat(system: str, user: str, max_tokens: int = 1024) -> str:
    body = json.dumps({
        "model": settings.ollama_model,
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": 0.2},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }).encode()
    req = urllib.request.Request(
        f"{settings.ollama_base_url.rstrip('/')}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode())
    return data.get("message", {}).get("content", "")


def _ollama_nl_to_sql(question: str) -> dict[str, Any]:
    system = SYSTEM_PROMPT + "\n\n" + _schema_snapshot()
    text = _ollama_chat(system, question, max_tokens=1024)
    reasoning, sql = _parse(text)
    return {"reasoning": reasoning, "sql": sql, "model": settings.ollama_model, "usage": {}}


def _ollama_summarize(prompt: str) -> str:
    return _ollama_chat("You summarize data concisely for a construction executive.", prompt, max_tokens=400).strip()


# ---- Public API ----------------------------------------------------------

def nl_to_sql(question: str) -> dict[str, Any]:
    if settings.llm_provider == "ollama":
        return _ollama_nl_to_sql(question)
    return _anthropic_nl_to_sql(question)


def summarize(question: str, sql: str, result: dict[str, Any]) -> str:
    preview_rows = result["rows"][:30]
    prompt = (
        f"User asked: {question}\n\n"
        f"SQL run:\n{sql}\n\n"
        f"Returned {len(result['rows'])} rows (columns: {', '.join(result['columns'])}).\n"
        f"Sample rows: {preview_rows}\n\n"
        "Give a crisp, executive-ready answer in 2-4 sentences. "
        "Highlight numbers and names. No fluff."
    )
    if settings.llm_provider == "ollama":
        return _ollama_summarize(prompt)
    return _anthropic_summarize(prompt)


def answer_question(question: str) -> dict[str, Any]:
    cache_parts = {
        "q": question.strip(),
        "schema": _schema_hash(),
        "provider": settings.llm_provider,
        "model": settings.anthropic_model if settings.llm_provider == "anthropic" else settings.ollama_model,
    }
    cached = cache.get(cache_parts)
    if cached is not None:
        cached["cached"] = True
        return cached

    plan = nl_to_sql(question)
    try:
        result = run_query(plan["sql"])
    except UnsafeSQLError as e:
        return {"error": f"unsafe_sql: {e}", "plan": plan}

    summary_text = summarize(question, plan["sql"], result)
    citations = _find_citations(result)
    out = {
        "plan": plan,
        "result": result,
        "summary": summary_text,
        "citations": citations,
        "cached": False,
    }
    cache.set_(cache_parts, out)
    return out
