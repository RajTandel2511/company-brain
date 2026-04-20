"""Dump columns for the key business tables so we can write tuned queries."""
from __future__ import annotations

import os
from pathlib import Path

import pyodbc
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

CONN_STR = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={os.environ['SPECTRUM_SQL_HOST']},{os.environ.get('SPECTRUM_SQL_PORT','1433')};"
    f"DATABASE={os.environ['SPECTRUM_SQL_DATABASE']};"
    f"UID={os.environ['SPECTRUM_SQL_USER']};PWD={os.environ['SPECTRUM_SQL_PASSWORD']};"
    "Encrypt=yes;TrustServerCertificate=yes;ApplicationIntent=ReadOnly;"
)

KEY_TABLES = [
    # Jobs
    "JC_JOB_MASTER_MC",
    "JC_PHASE_MASTER_MC",
    "JC_PHASE_SUMMARY_MC",
    "JC_PROJ_COST_HISTORY_MC",
    "JC_TRANSACTION_HISTORY_MC",
    # AR
    "CR_CUSTOMER_MASTER_MC",
    "CR_INVOICE_HEADER_MC",
    "CR_INVOICE_DETAIL_MC",
    "CR_BILLING_HEADER_MC",
    "CR_OPEN_ITEMS_MC",
    # AP / Vendors
    "VN_VENDOR_MASTER_MC",
    "VN_GL_DISTRIBUTION_HEADER_MC",
    "VN_GL_DISTRIBUTION_DETAIL_MC",
    "VN_PAYMENT_HISTORY_MC",
    # PO
    "PO_PURCHASE_ORDER_HEADER_MC",
    "PO_PURCHASE_ORDER_DETAIL_MC",
    # Subcontracts
    "VN_SUBCONTRACT_MC",
    "VN_SUBCONTRACT_PHASE_MC",
    # Equipment
    "EC_EQUIPMENT_MASTER_MC",
    "EC_METER_HISTORY_MC",
    # Payroll
    "PR_EMPLOYEE_MASTER_1_MC",
    "PR_TIME_CARD_HISTORY_MC",
    # Document imaging
    "DI_MASTER_MC",
    "DI_IMAGE_XREF",
]

conn = pyodbc.connect(CONN_STR, timeout=10, readonly=True)
cur = conn.cursor()

out = Path(__file__).resolve().parents[1] / "key_tables.md"
with out.open("w", encoding="utf-8") as f:
    for t in KEY_TABLES:
        cur.execute(
            "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH "
            "FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ? ORDER BY ORDINAL_POSITION",
            (t,),
        )
        rows = cur.fetchall()
        if not rows:
            f.write(f"\n## `{t}`  — NOT FOUND\n")
            continue
        # row count
        try:
            cur.execute(
                "SELECT SUM(p.rows) FROM sys.partitions p JOIN sys.tables tt ON tt.object_id = p.object_id "
                "WHERE tt.name = ? AND p.index_id IN (0,1)",
                (t,),
            )
            n = cur.fetchone()[0] or 0
        except Exception:
            n = "?"
        f.write(f"\n## `{t}` — {n:,} rows\n")
        for name, dtype, nullable, maxlen in rows:
            tag = dtype + (f"({maxlen})" if maxlen and maxlen > 0 else "")
            null = "" if nullable == "YES" else " NOT NULL"
            f.write(f"- {name}  `{tag}{null}`\n")

print(f"Wrote {out}")
