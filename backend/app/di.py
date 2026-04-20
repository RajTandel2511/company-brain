"""Spectrum Document Imaging (DI) integration.

DI_MASTER_MC stores a structured catalog of every document Spectrum tracks:
  - Cabinet  : top-level category (JOB, VENDOR, CUSTOMER, EMPLOYEE, CONTRACTS…)
  - Drawer   : sub-category (AP INVOICE, CORRESPONDENCE, TIMECARDS, CHANGE ORDERS…)
  - Folder   : the entity code (job_number, vendor_code, customer_code…)
  - Reference: the transaction reference (invoice number, week-ending date…)

DI_IMAGE_XREF maps each DI entry → a Document_ID in DI_IMAGE_MASTER which
has Image_Filename and Image_Description (the actual scanned file reference).

We expose counts + raw records for the Job Command Center / vendor / customer
views so users can see what Spectrum already has on file for an entity.
"""
from __future__ import annotations

from typing import Any

from .config import settings
from .db import run_query

CO = settings.spectrum_company_code


def _counts(where_sql: str, params: tuple) -> list[dict[str, Any]]:
    sql = f"""
        SELECT LTRIM(RTRIM(Drawer)) AS Drawer, COUNT(*) AS N
        FROM dbo.DI_MASTER_MC
        WHERE Company_Code = ? {where_sql}
        GROUP BY Drawer
        ORDER BY N DESC
    """
    return run_query(sql, (CO, *params))["rows"]


def _records(where_sql: str, params: tuple, limit: int = 100) -> list[dict[str, Any]]:
    sql = f"""
        SELECT TOP {int(limit)}
            LTRIM(RTRIM(m.Cabinet))  AS Cabinet,
            LTRIM(RTRIM(m.Drawer))   AS Drawer,
            LTRIM(RTRIM(m.Folder))   AS Folder,
            LTRIM(RTRIM(m.Reference)) AS Reference,
            m.Transaction_Description AS Description,
            m.Keywords,
            im.Image_Filename        AS Filename,
            im.Image_Description     AS File_Description
        FROM dbo.DI_MASTER_MC m
        LEFT JOIN dbo.DI_IMAGE_XREF x ON x.Transaction_ID = m.Transaction_ID
        LEFT JOIN dbo.DI_IMAGE_MASTER im ON im.Document_ID = x.Document_ID
        WHERE m.Company_Code = ? {where_sql}
        ORDER BY m.Reference DESC
    """
    return run_query(sql, (CO, *params))["rows"]


def for_job(job_number: str) -> dict[str, Any]:
    jn = job_number.strip()
    # Folder may be stored trimmed or padded — match both
    where = "AND Cabinet = 'JOB' AND LTRIM(RTRIM(Folder)) = ?"
    return {
        "job_number": jn,
        "counts_by_drawer": _counts(where, (jn,)),
        "recent": _records(where, (jn,), limit=30),
    }


def for_vendor(vendor_code: str) -> dict[str, Any]:
    vc = vendor_code.strip().upper()
    where = "AND Cabinet = 'VENDOR' AND UPPER(LTRIM(RTRIM(Folder))) = ?"
    return {
        "vendor_code": vc,
        "counts_by_drawer": _counts(where, (vc,)),
        "recent": _records(where, (vc,), limit=30),
    }


def for_customer(customer_code: str) -> dict[str, Any]:
    cc = customer_code.strip().upper()
    where = "AND Cabinet = 'CUSTOMER' AND UPPER(LTRIM(RTRIM(Folder))) = ?"
    return {
        "customer_code": cc,
        "counts_by_drawer": _counts(where, (cc,)),
        "recent": _records(where, (cc,), limit=30),
    }


def search_filenames(query: str, limit: int = 50) -> list[dict[str, Any]]:
    q = f"%{query.strip()}%"
    sql = f"""
        SELECT TOP {int(limit)}
            LTRIM(RTRIM(m.Cabinet))   AS Cabinet,
            LTRIM(RTRIM(m.Drawer))    AS Drawer,
            LTRIM(RTRIM(m.Folder))    AS Folder,
            LTRIM(RTRIM(m.Reference)) AS Reference,
            m.Transaction_Description AS Description,
            im.Image_Filename         AS Filename
        FROM dbo.DI_MASTER_MC m
        JOIN dbo.DI_IMAGE_XREF x ON x.Transaction_ID = m.Transaction_ID
        JOIN dbo.DI_IMAGE_MASTER im ON im.Document_ID = x.Document_ID
        WHERE m.Company_Code = ?
          AND (im.Image_Filename LIKE ? OR im.Image_Description LIKE ? OR m.Transaction_Description LIKE ?)
        ORDER BY m.Reference DESC
    """
    return run_query(sql, (CO, q, q, q))["rows"]
