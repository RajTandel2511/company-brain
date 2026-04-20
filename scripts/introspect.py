"""Spectrum schema introspector.

Runs OUTSIDE Docker. Just needs pyodbc + your .env. Dumps a markdown summary
to `schema_snapshot.md` that you can paste back so we can tune queries.

Usage:
    pip install pyodbc python-dotenv
    python scripts/introspect.py

Safe by design:
- Only INFORMATION_SCHEMA and sys.* reads.
- No data rows; only table names, column metadata, and approximate row counts.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    import pyodbc
except ImportError:
    sys.exit("Missing pyodbc. Run: pip install pyodbc python-dotenv")

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

HOST = os.environ["SPECTRUM_SQL_HOST"]
PORT = os.environ.get("SPECTRUM_SQL_PORT", "1433")
DB = os.environ.get("SPECTRUM_SQL_DATABASE", "Spectrum")
USER = os.environ["SPECTRUM_SQL_USER"]
PWD = os.environ["SPECTRUM_SQL_PASSWORD"]

CONN_STR = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={HOST},{PORT};DATABASE={DB};UID={USER};PWD={PWD};"
    "Encrypt=yes;TrustServerCertificate=yes;ApplicationIntent=ReadOnly;"
)

OUT = Path(__file__).resolve().parents[1] / "schema_snapshot.md"


def main():
    print(f"Connecting to {HOST}:{PORT} / {DB} as {USER}…")
    conn = pyodbc.connect(CONN_STR, timeout=10, readonly=True)
    cur = conn.cursor()

    cur.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE IN ('BASE TABLE','VIEW')
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)
    tables = cur.fetchall()

    cur.execute("""
        SELECT s.name AS schema_name, t.name AS table_name, SUM(p.rows) AS row_count
        FROM sys.tables t
        JOIN sys.schemas s ON s.schema_id = t.schema_id
        JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0,1)
        GROUP BY s.name, t.name
    """)
    counts = {(r.schema_name, r.table_name): int(r.row_count) for r in cur.fetchall()}

    cur.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE,
               IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
    """)
    cols: dict[tuple[str, str], list[tuple]] = {}
    for r in cur.fetchall():
        cols.setdefault((r.TABLE_SCHEMA, r.TABLE_NAME), []).append(
            (r.COLUMN_NAME, r.DATA_TYPE, r.IS_NULLABLE, r.CHARACTER_MAXIMUM_LENGTH)
        )

    lines: list[str] = []
    lines.append(f"# Spectrum schema snapshot — {DB} @ {HOST}\n")
    lines.append(f"**Total objects:** {len(tables)}\n")

    # Top 50 largest tables
    top = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:50]
    lines.append("\n## Top 50 tables by row count\n")
    lines.append("| schema | table | rows |")
    lines.append("|---|---|---:|")
    for (s, t), n in top:
        lines.append(f"| {s} | {t} | {n:,} |")

    # Keyword grouping — common Spectrum domains
    KEYWORDS = {
        "Jobs / Project": ["job", "phase", "costcode", "wbs", "project"],
        "AR / Billing": ["arinvoice", "arpay", "armaster", "billing", "invoice", "customer"],
        "AP / PO / Commitments": ["apinvoice", "appay", "po", "purchase", "vendor", "subcontract", "commit"],
        "Payroll / HR": ["pay", "employee", "timecard", "labor", "deduction"],
        "Equipment": ["equip", "fleet", "meter", "fuel"],
        "GL / Finance": ["gl", "account", "ledger", "journal", "budget"],
        "Service / Work Orders": ["wo", "workorder", "service", "dispatch"],
    }
    lines.append("\n## Tables grouped by domain (substring match, case-insensitive)\n")
    all_names = [(s, t) for s, t, _ in tables]
    for label, keys in KEYWORDS.items():
        hits = [
            (s, t) for s, t in all_names
            if any(k in t.lower() for k in keys)
        ]
        if not hits:
            continue
        lines.append(f"\n### {label}  ({len(hits)})\n")
        for s, t in hits[:60]:
            n = counts.get((s, t))
            size = f" — {n:,} rows" if n is not None else ""
            lines.append(f"- `{s}.{t}`{size}")

    # Columns for top-20 by row count (abbreviated)
    lines.append("\n## Columns — top 20 largest tables\n")
    for (s, t), n in top[:20]:
        lines.append(f"\n### `{s}.{t}` — {n:,} rows")
        for name, dtype, nullable, maxlen in cols.get((s, t), [])[:60]:
            tag = f"{dtype}" + (f"({maxlen})" if maxlen and maxlen > 0 else "")
            null = "" if nullable == "YES" else " NOT NULL"
            lines.append(f"- {name}  `{tag}{null}`")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}  ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
