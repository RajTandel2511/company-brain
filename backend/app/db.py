"""Read-only SQL Server client for Trimble Spectrum.

Enforces SELECT-only queries at the application layer regardless of DB perms,
applies a hard row limit, and wraps every execution in a read-only transaction.
"""
from __future__ import annotations

import re
from contextlib import contextmanager
from typing import Any

import pyodbc
import sqlparse

from .config import settings

MAX_ROWS = 5000
STATEMENT_TIMEOUT_SECONDS = 30

_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|MERGE|EXEC|EXECUTE|GRANT|REVOKE|BACKUP|RESTORE|SHUTDOWN|USE|INTO)\b",
    re.IGNORECASE,
)


class UnsafeSQLError(ValueError):
    pass


def _connection_string() -> str:
    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={settings.spectrum_sql_host},{settings.spectrum_sql_port};"
        f"DATABASE={settings.spectrum_sql_database};"
        f"UID={settings.spectrum_sql_user};"
        f"PWD={settings.spectrum_sql_password};"
        f"Encrypt={settings.spectrum_sql_encrypt};"
        f"TrustServerCertificate={settings.spectrum_sql_trust_cert};"
        "ApplicationIntent=ReadOnly;"
    )


@contextmanager
def get_connection():
    conn = pyodbc.connect(_connection_string(), timeout=10, readonly=True)
    try:
        conn.autocommit = False
        yield conn
    finally:
        conn.close()


def assert_safe_sql(sql: str) -> str:
    """Raise if the SQL is anything other than a single SELECT/WITH statement."""
    statements = [s for s in sqlparse.parse(sql) if str(s).strip()]
    if len(statements) != 1:
        raise UnsafeSQLError("Exactly one statement allowed.")
    stmt = statements[0]
    first_token = stmt.token_first(skip_cm=True)
    if not first_token:
        raise UnsafeSQLError("Empty statement.")
    kw = first_token.normalized.upper()
    if kw not in ("SELECT", "WITH"):
        raise UnsafeSQLError(f"Only SELECT/WITH allowed, got {kw}.")
    # Strip SQL comments and string literals before keyword-checking, so English
    # words like "Use" inside a comment don't false-match the USE keyword.
    stripped = sqlparse.format(sql, strip_comments=True)
    # Also blank out string literals so words inside 'quoted strings' don't match.
    stripped = re.sub(r"'[^']*'", "''", stripped)
    if _FORBIDDEN.search(stripped):
        raise UnsafeSQLError("Forbidden keyword detected.")
    if ";" in sql.rstrip().rstrip(";"):
        raise UnsafeSQLError("Multiple statements not allowed.")
    return sql


def run_query(sql: str, params: tuple = ()) -> dict[str, Any]:
    assert_safe_sql(sql)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SET LOCK_TIMEOUT {STATEMENT_TIMEOUT_SECONDS * 1000};")
        cursor.execute(sql, params)
        columns = [c[0] for c in cursor.description] if cursor.description else []
        rows = []
        for i, row in enumerate(cursor):
            if i >= MAX_ROWS:
                break
            rows.append({col: _coerce(val) for col, val in zip(columns, row)})
        return {"columns": columns, "rows": rows, "truncated": len(rows) >= MAX_ROWS}


def _coerce(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, (bytes, bytearray)):
        return v.hex()
    if hasattr(v, "isoformat"):
        return v.isoformat()
    try:
        import decimal
        if isinstance(v, decimal.Decimal):
            return float(v)
    except ImportError:
        pass
    return v


def list_tables() -> list[dict[str, str]]:
    sql = """
        SELECT TABLE_SCHEMA AS schema_name, TABLE_NAME AS table_name, TABLE_TYPE AS kind
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE IN ('BASE TABLE','VIEW')
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """
    return run_query(sql)["rows"]


def describe_table(schema: str, table: str) -> list[dict[str, Any]]:
    sql = """
        SELECT COLUMN_NAME AS name, DATA_TYPE AS type, IS_NULLABLE AS nullable,
               CHARACTER_MAXIMUM_LENGTH AS max_len
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
    """
    return run_query(sql, (schema, table))["rows"]
