"""Follow-the-money views — trace a vendor, invoice, or employee-expense
report all the way through its Spectrum distributions.

Core insight: `VN_GL_DISTRIBUTION_HEADER_MC` holds one row per AP invoice;
`VN_GL_DISTRIBUTION_DETAIL_MC` has one row per job/phase/cost-type split of
that invoice. Summing the detail rows must equal the header Invoice_Amount
(modulo tax). When an invoice hits many jobs — common for employee expense
reimbursements — the header total is misleading; the detail is the truth.
"""
from __future__ import annotations

from typing import Any

from . import docintel
from .config import settings
from .db import run_query

CO = settings.spectrum_company_code


def invoice_trace(vendor_code: str, invoice_number: str) -> dict[str, Any]:
    """Every detail line for one invoice, grouped by job/phase/cost_type."""
    vc = vendor_code.strip()
    inv = invoice_number.strip()

    header = run_query(
        """
        SELECT TOP 1
            LTRIM(RTRIM(h.Vendor_Code)) AS Vendor_Code,
            LTRIM(RTRIM(h.Vendor_Name)) AS Vendor_Name,
            h.Invoice_Number,
            h.Invoice_Type_Code,
            h.Invoice_Amount,
            h.Check_Number,
            h.Check_Date,
            h.Status,
            h.Remarks
        FROM dbo.VN_GL_DISTRIBUTION_HEADER_MC h
        WHERE h.Company_Code = ?
          AND LTRIM(RTRIM(h.Vendor_Code)) = ?
          AND LTRIM(RTRIM(h.Invoice_Number)) = ?
        """,
        (CO, vc, inv),
    )["rows"]
    if not header:
        return {"found": False, "vendor_code": vc, "invoice_number": inv}

    lines = run_query(
        """
        SELECT
            Sequence,
            LTRIM(RTRIM(Job_Number))   AS Job_Number,
            LTRIM(RTRIM(Phase_Code))   AS Phase_Code,
            Cost_Type,
            Debit_Amount - Credit_Amount AS Amount,
            Quantity,
            LTRIM(RTRIM(Remarks))      AS Remarks,
            LTRIM(RTRIM(Item_Code))    AS Item_Code,
            LTRIM(RTRIM(Item_Desc))    AS Item_Desc,
            LTRIM(RTRIM(WO_Number))    AS WO_Number
        FROM dbo.VN_GL_DISTRIBUTION_DETAIL_MC
        WHERE Company_Code = ?
          AND LTRIM(RTRIM(Vendor_Code)) = ?
          AND LTRIM(RTRIM(Invoice_Number)) = ?
        ORDER BY Sequence
        """,
        (CO, vc, inv),
    )["rows"]

    # Rollups
    by_job: dict[str, float] = {}
    by_cost_type: dict[str, float] = {}
    for ln in lines:
        amt = float(ln.get("Amount") or 0)
        j = ln.get("Job_Number") or "(none)"
        ct = (ln.get("Cost_Type") or "").strip() or "(none)"
        by_job[j] = by_job.get(j, 0) + amt
        by_cost_type[ct] = by_cost_type.get(ct, 0) + amt

    lines_total = sum(by_job.values())
    header_total = float(header[0]["Invoice_Amount"] or 0)

    # Cross-link: NAS files whose CONTENT mentions this invoice number
    # (covers scanned invoices, receipts, emails — whatever the doc-intel
    # extractor has seen so far).
    try:
        linked_files = docintel.files_for_entity("ap_invoice", inv, limit=50)
    except Exception:
        linked_files = []

    return {
        "found": True,
        "header": header[0],
        "lines": lines,
        "rollup_by_job":       [{"job": k, "amount": v} for k, v in sorted(by_job.items(), key=lambda kv: -kv[1])],
        "rollup_by_cost_type": [{"cost_type": k, "amount": v} for k, v in sorted(by_cost_type.items(), key=lambda kv: -kv[1])],
        "line_count": len(lines),
        "lines_total": lines_total,
        "header_total": header_total,
        "reconciliation_delta": round(header_total - lines_total, 2),
        "linked_files": linked_files,
    }


def list_vendors(search: str = "", limit: int = 100,
                 employees_only: bool = False) -> list[dict[str, Any]]:
    """Quick lookup list for the sidebar. Ranks by recent-invoice date + balance."""
    q = f"%{search.strip()}%" if search.strip() else "%"
    return run_query(
        f"""
        SELECT TOP {int(limit)}
            LTRIM(RTRIM(Vendor_Code)) AS Vendor_Code,
            LTRIM(RTRIM(Vendor_Name)) AS Vendor_Name,
            LTRIM(RTRIM(Type))        AS Vendor_Type,
            Balance,
            Date_Last_Invoice,
            CASE WHEN Social_Sec_Number IS NOT NULL
                  AND LEN(LTRIM(RTRIM(Social_Sec_Number))) > 0
                 THEN 1 ELSE 0 END AS Has_SSN
        FROM dbo.VN_VENDOR_MASTER_MC
        WHERE Company_Code = ?
          AND (LTRIM(RTRIM(Vendor_Name)) LIKE ? OR LTRIM(RTRIM(Vendor_Code)) LIKE ?)
          { "AND (UPPER(LTRIM(RTRIM(Type))) = 'EMPL' OR (Social_Sec_Number IS NOT NULL AND LEN(LTRIM(RTRIM(Social_Sec_Number))) > 0))"
            if employees_only else "" }
        ORDER BY Date_Last_Invoice DESC, ABS(Balance) DESC
        """,
        (CO, q, q),
    )["rows"]


def vendor_spend(vendor_code: str, days: int = 365) -> dict[str, Any]:
    """Everything posted from this vendor in the last N days: invoices,
    jobs hit, breakdown by cost type. Includes employee-detection heuristic."""
    vc = vendor_code.strip()

    vendor = run_query(
        """
        SELECT TOP 1
            LTRIM(RTRIM(Vendor_Code)) AS Vendor_Code,
            LTRIM(RTRIM(Vendor_Name)) AS Vendor_Name,
            LTRIM(RTRIM(Type))        AS Vendor_Type,
            Social_Sec_Number,
            Balance,
            Date_Last_Invoice,
            Date_Last_Payment
        FROM dbo.VN_VENDOR_MASTER_MC
        WHERE Company_Code = ? AND LTRIM(RTRIM(Vendor_Code)) = ?
        """,
        (CO, vc),
    )["rows"]

    # Employee heuristic: vendor name matches an employee's FULL name
    # (either "First Last" or "Last First"). Last-name-only was too loose —
    # it caught namesakes. We also consider vendor type='EMPL' or a populated
    # Social_Sec_Number as strong signals even without a name match.
    is_employee = False
    matched_employee = None
    if vendor:
        v = vendor[0]
        vname = (v.get("Vendor_Name") or "").strip().upper()
        has_ssn = bool((v.get("Social_Sec_Number") or "").strip())
        vtype = (v.get("Vendor_Type") or "").strip().upper()
        if vname:
            emp_row = run_query(
                """
                SELECT TOP 1
                    LTRIM(RTRIM(Employee_Code)) AS Employee_Code,
                    LTRIM(RTRIM(First_Name))    AS First_Name,
                    LTRIM(RTRIM(Last_Name))     AS Last_Name
                FROM dbo.PR_EMPLOYEE_MASTER_1_MC
                WHERE Company_Code = ?
                  AND (UPPER(LTRIM(RTRIM(First_Name)) + ' ' + LTRIM(RTRIM(Last_Name))) = ?
                    OR UPPER(LTRIM(RTRIM(Last_Name)) + ' ' + LTRIM(RTRIM(First_Name))) = ?
                    OR UPPER(LTRIM(RTRIM(Last_Name)) + ', ' + LTRIM(RTRIM(First_Name))) = ?)
                """,
                (CO, vname, vname, vname),
            )["rows"]
            if emp_row:
                is_employee = True
                matched_employee = emp_row[0]
        if not is_employee and (has_ssn or vtype in ("EMPL", "1099")):
            # Strong signal: SSN present OR explicit employee type
            is_employee = True

    # Recent invoices + their per-invoice totals
    invoices = run_query(
        """
        SELECT TOP 100
            h.Invoice_Number,
            h.Invoice_Type_Code,
            h.Invoice_Amount,
            h.Check_Number,
            h.Check_Date,
            h.Remarks,
            SUM(d.Debit_Amount - d.Credit_Amount) AS Line_Total,
            COUNT(*) AS Line_Count,
            COUNT(DISTINCT LTRIM(RTRIM(d.Job_Number))) AS Jobs_Hit
        FROM dbo.VN_GL_DISTRIBUTION_HEADER_MC h
        LEFT JOIN dbo.VN_GL_DISTRIBUTION_DETAIL_MC d
          ON d.Company_Code = h.Company_Code
         AND d.Vendor_Code = h.Vendor_Code
         AND d.Invoice_Number = h.Invoice_Number
         AND d.Invoice_Type_Code = h.Invoice_Type_Code
        WHERE h.Company_Code = ?
          AND LTRIM(RTRIM(h.Vendor_Code)) = ?
          AND COALESCE(h.Check_Date, h.Date_Stamp) >= DATEADD(day, ?, GETDATE())
        GROUP BY h.Invoice_Number, h.Invoice_Type_Code, h.Invoice_Amount,
                 h.Check_Number, h.Check_Date, h.Date_Stamp, h.Remarks
        ORDER BY COALESCE(h.Check_Date, h.Date_Stamp) DESC
        """,
        (CO, vc, -days),
    )["rows"]

    # Per-job breakdown of this vendor's spend in the window
    by_job = run_query(
        """
        SELECT TOP 30
            LTRIM(RTRIM(d.Job_Number)) AS Job_Number,
            SUM(d.Debit_Amount - d.Credit_Amount) AS Amount,
            COUNT(DISTINCT h.Invoice_Number)       AS Invoices
        FROM dbo.VN_GL_DISTRIBUTION_HEADER_MC h
        JOIN dbo.VN_GL_DISTRIBUTION_DETAIL_MC d
          ON d.Company_Code = h.Company_Code
         AND d.Vendor_Code = h.Vendor_Code
         AND d.Invoice_Number = h.Invoice_Number
         AND d.Invoice_Type_Code = h.Invoice_Type_Code
        WHERE h.Company_Code = ?
          AND LTRIM(RTRIM(d.Vendor_Code)) = ?
          AND COALESCE(h.Check_Date, h.Date_Stamp) >= DATEADD(day, ?, GETDATE())
          AND LTRIM(RTRIM(d.Job_Number)) <> ''
        GROUP BY LTRIM(RTRIM(d.Job_Number))
        ORDER BY SUM(d.Debit_Amount - d.Credit_Amount) DESC
        """,
        (CO, vc, -days),
    )["rows"]

    by_cost_type = run_query(
        """
        SELECT
            d.Cost_Type,
            SUM(d.Debit_Amount - d.Credit_Amount) AS Amount,
            COUNT(*) AS Lines
        FROM dbo.VN_GL_DISTRIBUTION_HEADER_MC h
        JOIN dbo.VN_GL_DISTRIBUTION_DETAIL_MC d
          ON d.Company_Code = h.Company_Code
         AND d.Vendor_Code = h.Vendor_Code
         AND d.Invoice_Number = h.Invoice_Number
         AND d.Invoice_Type_Code = h.Invoice_Type_Code
        WHERE h.Company_Code = ?
          AND LTRIM(RTRIM(d.Vendor_Code)) = ?
          AND COALESCE(h.Check_Date, h.Date_Stamp) >= DATEADD(day, ?, GETDATE())
        GROUP BY d.Cost_Type
        ORDER BY SUM(d.Debit_Amount - d.Credit_Amount) DESC
        """,
        (CO, vc, -days),
    )["rows"]

    # Total spend in window, by summing distribution detail
    totals = run_query(
        """
        SELECT
            SUM(d.Debit_Amount - d.Credit_Amount) AS Total_Spend,
            COUNT(DISTINCT h.Invoice_Number)       AS Invoice_Count,
            COUNT(DISTINCT LTRIM(RTRIM(d.Job_Number))) AS Distinct_Jobs
        FROM dbo.VN_GL_DISTRIBUTION_HEADER_MC h
        JOIN dbo.VN_GL_DISTRIBUTION_DETAIL_MC d
          ON d.Company_Code = h.Company_Code
         AND d.Vendor_Code = h.Vendor_Code
         AND d.Invoice_Number = h.Invoice_Number
         AND d.Invoice_Type_Code = h.Invoice_Type_Code
        WHERE h.Company_Code = ?
          AND LTRIM(RTRIM(d.Vendor_Code)) = ?
          AND COALESCE(h.Check_Date, h.Date_Stamp) >= DATEADD(day, ?, GETDATE())
        """,
        (CO, vc, -days),
    )["rows"]

    # NAS docs mentioning this vendor by code
    try:
        from . import docintel as _di
        linked_files = _di.files_for_entity("vendor", vc, limit=50)
    except Exception:
        linked_files = []

    return {
        "vendor": vendor[0] if vendor else None,
        "is_employee_reimbursement": is_employee,
        "matched_employee": matched_employee,
        "window_days": days,
        "totals": totals[0] if totals else {},
        "invoices": invoices,
        "by_job": by_job,
        "by_cost_type": by_cost_type,
        "linked_files": linked_files,
    }
