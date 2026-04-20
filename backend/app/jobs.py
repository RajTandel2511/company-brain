"""Job Command Center — aggregate everything about one job across Spectrum + NAS."""
from __future__ import annotations

from typing import Any

from . import di, docintel, files
from .config import settings
from .db import run_query


CO = settings.spectrum_company_code


def _one(sql: str, params: tuple = ()) -> dict[str, Any] | None:
    r = run_query(sql, params)
    return r["rows"][0] if r["rows"] else None


def _many(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    return run_query(sql, params)["rows"]


def summary(job_number: str) -> dict[str, Any]:
    job_number = job_number.strip()
    # Use LIKE because Spectrum stores Job_Number padded with spaces (e.g. '     19.50').
    # We match against both padded and trimmed forms.
    pattern = f"%{job_number}"

    master = _one(
        """
        SELECT TOP 1
            LTRIM(RTRIM(Job_Number))       AS Job_Number,
            LTRIM(RTRIM(Job_Description))  AS Job_Description,
            LTRIM(RTRIM(Customer_Code))    AS Customer_Code,
            LTRIM(RTRIM(Project_Manager))  AS Project_Manager,
            LTRIM(RTRIM(Superintendent))   AS Superintendent,
            LTRIM(RTRIM(Estimator))        AS Estimator,
            LTRIM(RTRIM(City)) + ', ' + LTRIM(RTRIM(State)) AS Location,
            Status_Code,
            Original_Contract,
            Start_Date,
            Est_Complete_Date,
            Projected_Complete_Date,
            Create_Date
        FROM dbo.JC_JOB_MASTER_MC
        WHERE Company_Code = ? AND LTRIM(RTRIM(Job_Number)) = ?
        """,
        (CO, job_number),
    )
    if not master:
        return {"job_number": job_number, "found": False}

    # Customer name
    cust = None
    if master.get("Customer_Code"):
        cust = _one(
            "SELECT TOP 1 LTRIM(RTRIM(Name)) AS Customer_Name, Balance, Credit_Limit "
            "FROM dbo.CR_CUSTOMER_MASTER_MC WHERE Company_Code = ? AND Customer_Code = ?",
            (CO, master["Customer_Code"]),
        )

    # Actual cost + hours to date
    cost = _one(
        """
        SELECT
            SUM(Tran_Amount) AS Actual_Cost,
            SUM(Total_Hours) AS Total_Hours,
            COUNT(*) AS Tran_Count,
            MAX(Tran_Date_Text) AS Last_Tran_Date
        FROM dbo.JC_TRANSACTION_HISTORY_MC
        WHERE Company_Code = ? AND LTRIM(RTRIM(Job_Number)) = ?
        """,
        (CO, job_number),
    ) or {}

    # Actual cost by cost type (L=Labor, M=Material, S=Sub, E=Equip, O=Other — Spectrum convention)
    cost_by_type = _many(
        """
        SELECT Cost_Type, SUM(Tran_Amount) AS Amount, SUM(Total_Hours) AS Hours
        FROM dbo.JC_TRANSACTION_HISTORY_MC
        WHERE Company_Code = ? AND LTRIM(RTRIM(Job_Number)) = ?
        GROUP BY Cost_Type
        ORDER BY SUM(Tran_Amount) DESC
        """,
        (CO, job_number),
    )

    # Latest billing application
    last_bill = _one(
        """
        SELECT TOP 1
            Application_Number,
            Period_End_Date,
            Revised_Contract_Amount,
            Complete_To_Date,
            Amount_Due,
            Retention_Amount
        FROM dbo.CR_BILLING_HEADER_MC
        WHERE Company_Code = ? AND Job_Number LIKE ?
        ORDER BY Period_End_Date DESC
        """,
        (CO, pattern),
    )

    # Outstanding AR for this job
    ar = _one(
        """
        SELECT
            COUNT(*) AS Open_Invoice_Count,
            SUM(Invoice_Extension) AS Billed_Total,
            MAX(DATEDIFF(day, Invoice_Date, GETDATE())) AS Oldest_Age_Days
        FROM dbo.CR_INVOICE_HEADER_MC
        WHERE Company_Code = ? AND Job_Number LIKE ?
          AND Invoice_Extension > 0
        """,
        (CO, pattern),
    ) or {}

    # AP lines posted to THIS job specifically — every one of them, tagged by
    # whether the vendor is really an employee (expense reimbursement) or a
    # true outside vendor.
    #
    # Employee detection (this company's conventions): vendor Type = 'EMPL',
    # or the vendor's Vendor_Name matches an employee full name in
    # PR_EMPLOYEE_MASTER_1_MC. NOTE: Social_Sec_Number on VN_VENDOR_MASTER_MC
    # is populated for nearly every vendor (used as Tax ID / EIN for 1099
    # reporting), so it's NOT a reliable employee signal here.
    #
    # IMPORTANT: we sum the detail rows (Debit - Credit) — that's the amount
    # truly attributed to this job. An invoice's header total can be much
    # larger when the invoice is split across many jobs (employee expense
    # reports especially).
    recent_ap = _many(
        """
        WITH emp_vendors AS (
            SELECT DISTINCT LTRIM(RTRIM(v.Vendor_Code)) AS Vendor_Code
            FROM dbo.VN_VENDOR_MASTER_MC v
            LEFT JOIN dbo.PR_EMPLOYEE_MASTER_1_MC e
              ON e.Company_Code = v.Company_Code
             AND (
                  -- This company uses the same code for employee-as-vendor
                  LTRIM(RTRIM(v.Vendor_Code)) = LTRIM(RTRIM(e.Employee_Code))
               OR UPPER(LTRIM(RTRIM(v.Vendor_Name))) =
                      UPPER(LTRIM(RTRIM(e.First_Name)) + ' ' + LTRIM(RTRIM(e.Last_Name)))
               OR UPPER(LTRIM(RTRIM(v.Vendor_Name))) =
                      UPPER(LTRIM(RTRIM(e.Last_Name)) + ' ' + LTRIM(RTRIM(e.First_Name)))
               OR UPPER(LTRIM(RTRIM(v.Vendor_Name))) =
                      UPPER(LTRIM(RTRIM(e.Last_Name)) + ', ' + LTRIM(RTRIM(e.First_Name)))
               -- Vendor name contains both the employee's first and last name
               -- anywhere (handles middle initials and Last-Middle-First orderings)
               OR (LEN(LTRIM(RTRIM(e.First_Name))) >= 2
                   AND LEN(LTRIM(RTRIM(e.Last_Name))) >= 2
                   AND UPPER(LTRIM(RTRIM(v.Vendor_Name))) LIKE
                       '%' + UPPER(LTRIM(RTRIM(e.First_Name))) + '%'
                                + UPPER(LTRIM(RTRIM(e.Last_Name))) + '%')
               OR (LEN(LTRIM(RTRIM(e.First_Name))) >= 2
                   AND LEN(LTRIM(RTRIM(e.Last_Name))) >= 2
                   AND UPPER(LTRIM(RTRIM(v.Vendor_Name))) LIKE
                       '%' + UPPER(LTRIM(RTRIM(e.Last_Name))) + '%'
                                + UPPER(LTRIM(RTRIM(e.First_Name))) + '%')
             )
            WHERE v.Company_Code = ?
              AND (UPPER(LTRIM(RTRIM(v.Type))) IN ('EMPL', '1099')
                   OR e.Employee_Code IS NOT NULL)
        )
        SELECT TOP 2000
            h.Invoice_Number,
            LTRIM(RTRIM(h.Vendor_Code)) AS Vendor_Code,
            LTRIM(RTRIM(h.Vendor_Name)) AS Vendor_Name,
            h.Check_Date,
            h.Check_Number,
            h.Status,
            h.Invoice_Amount                       AS Invoice_Total,
            SUM(d.Debit_Amount - d.Credit_Amount)  AS Job_Amount,
            COUNT(*)                               AS Line_Count,
            MAX(LTRIM(RTRIM(d.Phase_Code)))        AS Phase_Code,
            MAX(d.Cost_Type)                       AS Cost_Type,
            MAX(LTRIM(RTRIM(d.Remarks)))           AS Remarks,
            CASE WHEN ev.Vendor_Code IS NOT NULL THEN 1 ELSE 0 END AS Is_Employee
        FROM dbo.VN_GL_DISTRIBUTION_HEADER_MC h
        JOIN dbo.VN_GL_DISTRIBUTION_DETAIL_MC d
          ON d.Company_Code = h.Company_Code
         AND d.Vendor_Code = h.Vendor_Code
         AND d.Invoice_Number = h.Invoice_Number
         AND d.Invoice_Type_Code = h.Invoice_Type_Code
        LEFT JOIN emp_vendors ev
          ON ev.Vendor_Code = LTRIM(RTRIM(h.Vendor_Code))
        WHERE h.Company_Code = ? AND LTRIM(RTRIM(d.Job_Number)) = ?
        GROUP BY h.Invoice_Number, h.Vendor_Code, h.Vendor_Name,
                 h.Check_Date, h.Check_Number, h.Status, h.Invoice_Amount,
                 ev.Vendor_Code
        ORDER BY h.Check_Date DESC
        """,
        (CO, CO, job_number),
    )

    # Labor in last 30 days
    recent_labor = _many(
        """
        SELECT TOP 20
            LTRIM(RTRIM(Employee_Code)) AS Employee_Code,
            SUM(Hours) AS Hours,
            SUM(Pay_Extension) AS Pay,
            MAX(Work_Date) AS Last_Work_Date
        FROM dbo.PR_TIME_CARD_HISTORY_MC
        WHERE Company_Code = ? AND LTRIM(RTRIM(Job_Number)) = ?
          AND Work_Date >= DATEADD(day, -30, GETDATE())
        GROUP BY Employee_Code
        ORDER BY SUM(Pay_Extension) DESC
        """,
        (CO, job_number),
    )

    # Open POs
    open_pos = _many(
        """
        SELECT TOP 15
            LTRIM(RTRIM(h.PO_Number))   AS PO_Number,
            LTRIM(RTRIM(h.Vendor_Code)) AS Vendor_Code,
            LTRIM(RTRIM(v.Vendor_Name)) AS Vendor_Name,
            h.PO_Date_List1 AS PO_Date,
            SUM(d.Line_Extension_List1)  AS PO_Total,
            SUM(d.Received_Extension)    AS Received_Total
        FROM dbo.PO_PURCHASE_ORDER_HEADER_MC h
        LEFT JOIN dbo.PO_PURCHASE_ORDER_DETAIL_MC d
          ON d.Company_Code = h.Company_Code AND d.PO_Number = h.PO_Number
        LEFT JOIN dbo.VN_VENDOR_MASTER_MC v
          ON v.Company_Code = h.Company_Code AND v.Vendor_Code = h.Vendor_Code
        WHERE h.Company_Code = ? AND LTRIM(RTRIM(h.Job_Number)) = ?
        GROUP BY h.PO_Number, h.Vendor_Code, v.Vendor_Name, h.PO_Date_List1
        ORDER BY h.PO_Date_List1 DESC
        """,
        (CO, job_number),
    )

    # Total AP attributed to this job (all time), split into vendor vs.
    # employee-expense buckets. Authoritative because it sums detail rows
    # (per-job split) rather than the invoice header total. Uses the same
    # employee-detection rule as recent_ap above (name-match on
    # PR_EMPLOYEE_MASTER_1_MC, plus vendor Type = 'EMPL').
    ap_totals = _many(
        """
        WITH emp_vendors AS (
            SELECT DISTINCT LTRIM(RTRIM(v.Vendor_Code)) AS Vendor_Code
            FROM dbo.VN_VENDOR_MASTER_MC v
            LEFT JOIN dbo.PR_EMPLOYEE_MASTER_1_MC e
              ON e.Company_Code = v.Company_Code
             AND (
                  -- This company uses the same code for employee-as-vendor
                  LTRIM(RTRIM(v.Vendor_Code)) = LTRIM(RTRIM(e.Employee_Code))
               OR UPPER(LTRIM(RTRIM(v.Vendor_Name))) =
                      UPPER(LTRIM(RTRIM(e.First_Name)) + ' ' + LTRIM(RTRIM(e.Last_Name)))
               OR UPPER(LTRIM(RTRIM(v.Vendor_Name))) =
                      UPPER(LTRIM(RTRIM(e.Last_Name)) + ' ' + LTRIM(RTRIM(e.First_Name)))
               OR UPPER(LTRIM(RTRIM(v.Vendor_Name))) =
                      UPPER(LTRIM(RTRIM(e.Last_Name)) + ', ' + LTRIM(RTRIM(e.First_Name)))
               -- Vendor name contains both the employee's first and last name
               -- anywhere (handles middle initials and Last-Middle-First orderings)
               OR (LEN(LTRIM(RTRIM(e.First_Name))) >= 2
                   AND LEN(LTRIM(RTRIM(e.Last_Name))) >= 2
                   AND UPPER(LTRIM(RTRIM(v.Vendor_Name))) LIKE
                       '%' + UPPER(LTRIM(RTRIM(e.First_Name))) + '%'
                                + UPPER(LTRIM(RTRIM(e.Last_Name))) + '%')
               OR (LEN(LTRIM(RTRIM(e.First_Name))) >= 2
                   AND LEN(LTRIM(RTRIM(e.Last_Name))) >= 2
                   AND UPPER(LTRIM(RTRIM(v.Vendor_Name))) LIKE
                       '%' + UPPER(LTRIM(RTRIM(e.Last_Name))) + '%'
                                + UPPER(LTRIM(RTRIM(e.First_Name))) + '%')
             )
            WHERE v.Company_Code = ?
              AND (UPPER(LTRIM(RTRIM(v.Type))) IN ('EMPL', '1099')
                   OR e.Employee_Code IS NOT NULL)
        )
        SELECT
            CASE WHEN ev.Vendor_Code IS NOT NULL THEN 1 ELSE 0 END AS Is_Employee,
            SUM(d.Debit_Amount - d.Credit_Amount) AS Total,
            COUNT(DISTINCT CAST(h.Vendor_Code AS VARCHAR(20)) + '|' + CAST(h.Invoice_Number AS VARCHAR(50))) AS Invoice_Count
        FROM dbo.VN_GL_DISTRIBUTION_HEADER_MC h
        JOIN dbo.VN_GL_DISTRIBUTION_DETAIL_MC d
          ON d.Company_Code = h.Company_Code
         AND d.Vendor_Code = h.Vendor_Code
         AND d.Invoice_Number = h.Invoice_Number
         AND d.Invoice_Type_Code = h.Invoice_Type_Code
        LEFT JOIN emp_vendors ev
          ON ev.Vendor_Code = LTRIM(RTRIM(h.Vendor_Code))
        WHERE h.Company_Code = ? AND LTRIM(RTRIM(d.Job_Number)) = ?
        GROUP BY CASE WHEN ev.Vendor_Code IS NOT NULL THEN 1 ELSE 0 END
        """,
        (CO, CO, job_number),
    )
    ap_vendor = next((r for r in ap_totals if not r.get("Is_Employee")), {}) or {}
    ap_employee = next((r for r in ap_totals if r.get("Is_Employee")), {}) or {}
    ap_total_row = {
        "Total": float(ap_vendor.get("Total") or 0) + float(ap_employee.get("Total") or 0),
        "Invoice_Count": int(ap_vendor.get("Invoice_Count") or 0) + int(ap_employee.get("Invoice_Count") or 0),
    }

    # Variance & health scoring
    original = float(master.get("Original_Contract") or 0)
    actual = float(cost.get("Actual_Cost") or 0) if cost else 0.0
    pct_spent = (actual / original * 100) if original else 0

    # NAS folder match
    nas_folder = files.find_job_folder(job_number)
    nas_preview = files.list_dir(nas_folder)[:12] if nas_folder else []

    # Spectrum DI — scanned documents linked to this job
    try:
        di_data = di.for_job(job_number)
    except Exception:
        di_data = {"counts_by_drawer": [], "recent": []}

    # Document intelligence — NAS files that MENTION this job *or* something
    # attached to this job (POs, AP invoices, customer) in their content.
    # Each row is labeled with why it matched so the UI can explain.
    linked_files = _linked_files_transitive(job_number, master.get("Customer_Code"))

    return {
        "job_number": job_number,
        "found": True,
        "master": master,
        "customer": cust,
        "financials": {
            "original_contract": original,
            "actual_cost": actual,
            "pct_spent": round(pct_spent, 1),
            "variance": original - actual,
            "total_hours": float(cost.get("Total_Hours") or 0) if cost else 0.0,
            "tran_count": int(cost.get("Tran_Count") or 0) if cost else 0,
        },
        "cost_by_type": cost_by_type,
        "last_billing": last_bill,
        "ar": ar,
        "ap_total": {
            "amount": float(ap_total_row.get("Total") or 0),
            "invoice_count": int(ap_total_row.get("Invoice_Count") or 0),
        },
        "ap_total_vendor": {
            "amount": float(ap_vendor.get("Total") or 0),
            "invoice_count": int(ap_vendor.get("Invoice_Count") or 0),
        },
        "ap_total_employee": {
            "amount": float(ap_employee.get("Total") or 0),
            "invoice_count": int(ap_employee.get("Invoice_Count") or 0),
        },
        "recent_ap": recent_ap,
        "recent_labor": recent_labor,
        "open_pos": open_pos,
        "nas": {"folder": nas_folder, "preview": nas_preview},
        "di": di_data,
        "linked_files": linked_files,
    }


def _linked_files_transitive(job_number: str, customer_code: str | None,
                             per_source_limit: int = 30) -> list[dict[str, Any]]:
    """Union NAS files linked to this job by direct job mention OR by PO/invoice/customer."""
    seen: dict[str, dict[str, Any]] = {}

    def add(files: list[dict[str, Any]], reason: str, tag: str) -> None:
        for f in files:
            p = f.get("path")
            if not p:
                continue
            row = seen.get(p)
            if row:
                # Keep earliest-discovered "why" but accumulate additional reasons
                if reason not in row["reasons"]:
                    row["reasons"].append(reason)
            else:
                seen[p] = {**f, "reasons": [reason], "primary_tag": tag}

    # 1) Direct job mention
    try:
        add(docintel.files_for_entity("job", job_number, limit=per_source_limit),
            f"mentions job {job_number}", "job")
    except Exception:
        pass

    # 2) Via any PO attached to this job
    try:
        po_numbers = [
            (r.get("PO_Number") or "").strip()
            for r in run_query(
                "SELECT LTRIM(RTRIM(PO_Number)) AS PO_Number FROM dbo.PO_PURCHASE_ORDER_HEADER_MC "
                "WHERE Company_Code = ? AND LTRIM(RTRIM(Job_Number)) = ?",
                (CO, job_number),
            )["rows"] if r.get("PO_Number")
        ]
        for po in po_numbers:
            try:
                add(docintel.files_for_entity("po", po, limit=10),
                    f"mentions PO {po} (this job)", "po")
            except Exception:
                continue
    except Exception:
        pass

    # 3) Via any AP invoice posted to this job
    try:
        inv_rows = run_query(
            """
            SELECT DISTINCT TOP 50 LTRIM(RTRIM(d.Invoice_Number)) AS Invoice_Number
            FROM dbo.VN_GL_DISTRIBUTION_DETAIL_MC d
            WHERE d.Company_Code = ? AND LTRIM(RTRIM(d.Job_Number)) = ?
            """,
            (CO, job_number),
        )["rows"]
        for r in inv_rows:
            inv = r.get("Invoice_Number")
            if not inv:
                continue
            try:
                add(docintel.files_for_entity("ap_invoice", inv, limit=5),
                    f"mentions AP invoice {inv} (this job)", "ap_invoice")
            except Exception:
                continue
    except Exception:
        pass

    # 4) Customer on this job (guarded — can be noisy for big customers)
    if customer_code:
        cc = customer_code.strip()
        try:
            add(docintel.files_for_entity("customer", cc, limit=15),
                f"mentions customer {cc}", "customer")
        except Exception:
            pass

    # Sort by modified desc, cap overall
    merged = sorted(seen.values(), key=lambda f: f.get("modified") or 0, reverse=True)
    return merged[:120]


def at_risk(limit: int = 20) -> list[dict[str, Any]]:
    """Active jobs flagged by variance or stale activity.

    Uses REVISED contract (max across all billing apps) rather than Original_Contract
    so change orders are respected — same rule as the Insights engine.
    """
    return run_query(
        f"""
        WITH costs AS (
            SELECT LTRIM(RTRIM(Job_Number)) AS Job_Number,
                   SUM(Tran_Amount) AS Actual_Cost,
                   MAX(TRY_CONVERT(date, Tran_Date_Text, 112)) AS Last_Cost_Date
            FROM dbo.JC_TRANSACTION_HISTORY_MC
            WHERE Company_Code = '{CO}'
            GROUP BY LTRIM(RTRIM(Job_Number))
        ),
        bill_agg AS (
            SELECT b.Job_Number,
                   MAX(b.Revised_Contract_Amount) AS Revised_Contract_Amount
            FROM dbo.CR_BILLING_HEADER_MC b
            WHERE b.Company_Code = '{CO}'
            GROUP BY b.Job_Number
        ),
        contracts AS (
            SELECT
                LTRIM(RTRIM(j.Job_Number))      AS Job_Number,
                LTRIM(RTRIM(j.Job_Description)) AS Job_Description,
                LTRIM(RTRIM(j.Project_Manager)) AS Project_Manager,
                j.Original_Contract,
                CASE
                    WHEN ba.Revised_Contract_Amount IS NOT NULL
                         AND ba.Revised_Contract_Amount > j.Original_Contract
                    THEN ba.Revised_Contract_Amount
                    ELSE j.Original_Contract
                END AS Revised_Contract
            FROM dbo.JC_JOB_MASTER_MC j
            LEFT JOIN bill_agg ba ON ba.Job_Number = j.Job_Number
            WHERE j.Company_Code = '{CO}' AND j.Status_Code = 'A' AND j.Original_Contract > 0
        )
        SELECT TOP {limit}
            con.Job_Number,
            con.Job_Description,
            con.Project_Manager,
            con.Original_Contract,
            con.Revised_Contract,
            c.Actual_Cost,
            CASE WHEN con.Revised_Contract > 0
                 THEN CAST(ISNULL(c.Actual_Cost, 0) / con.Revised_Contract * 100 AS decimal(10,1))
                 ELSE 0 END AS Pct_Spent,
            DATEDIFF(day, c.Last_Cost_Date, GETDATE()) AS Days_Since_Cost
        FROM contracts con
        LEFT JOIN costs c ON c.Job_Number = con.Job_Number
        ORDER BY
            CASE WHEN con.Revised_Contract > 0
                 THEN ISNULL(c.Actual_Cost, 0) / con.Revised_Contract ELSE 0 END DESC,
            Days_Since_Cost DESC
        """
    )["rows"]
