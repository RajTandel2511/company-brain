"""Insights engine — scan the company for things that need attention.

Each rule returns a list of Insight dicts with a severity and enough
structured data for the UI to render deep-links back to the relevant
Job Command Center or Files view.

Rules intentionally conservative so the morning briefing stays signal-heavy.
"""
from __future__ import annotations

from typing import Any, TypedDict

from . import ai
from .config import settings
from .db import run_query


CO = settings.spectrum_company_code


class Insight(TypedDict, total=False):
    id: str
    rule: str
    severity: str  # "critical" | "high" | "medium" | "low"
    title: str
    detail: str
    job_number: str
    customer_code: str
    vendor_code: str
    amount: float
    count: int


def _many(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    return run_query(sql, params)["rows"]


# --- Rules ----------------------------------------------------------------

def rule_over_budget() -> list[Insight]:
    """Over-budget = actual cost > revised contract (original + change orders).

    Uses the most recent CR_BILLING_HEADER_MC.Revised_Contract_Amount when
    available — that's the number Spectrum treats as current contract value.
    Falls back to Original_Contract only if no billing apps exist.
    """
    rows = _many(f"""
        WITH costs AS (
            SELECT LTRIM(RTRIM(Job_Number)) AS Job_Number, SUM(Tran_Amount) AS Actual_Cost
            FROM dbo.JC_TRANSACTION_HISTORY_MC
            WHERE Company_Code = '{CO}'
            GROUP BY LTRIM(RTRIM(Job_Number))
        ),
        bill_agg AS (
            -- Use MAX across all billing apps: a job can have multiple billing
            -- streams (phases, supplements). The biggest revised contract across
            -- them is the true current contract value.
            SELECT b.Job_Number,
                   MAX(b.Revised_Contract_Amount) AS Revised_Contract_Amount,
                   MAX(b.Change_Order_Total)      AS Change_Order_Total
            FROM dbo.CR_BILLING_HEADER_MC b
            WHERE b.Company_Code = '{CO}'
            GROUP BY b.Job_Number
        ),
        contracts AS (
            SELECT
                LTRIM(RTRIM(j.Job_Number)) AS Job_Number,
                -- Use the greater of (Original_Contract, MAX(Revised) from bills)
                -- so we never flag a job because one small supplemental bill had a
                -- tiny revised number.
                CASE
                    WHEN ba.Revised_Contract_Amount IS NOT NULL
                         AND ba.Revised_Contract_Amount > j.Original_Contract
                    THEN ba.Revised_Contract_Amount
                    ELSE j.Original_Contract
                END AS Revised_Contract,
                j.Original_Contract,
                ISNULL(ba.Change_Order_Total, 0) AS Change_Order_Total
            FROM dbo.JC_JOB_MASTER_MC j
            LEFT JOIN bill_agg ba ON ba.Job_Number = j.Job_Number
            WHERE j.Company_Code = '{CO}' AND j.Status_Code = 'A'
        )
        SELECT TOP 10
            con.Job_Number,
            LTRIM(RTRIM(j.Job_Description)) AS Job_Description,
            con.Original_Contract,
            con.Change_Order_Total,
            con.Revised_Contract,
            c.Actual_Cost,
            c.Actual_Cost - con.Revised_Contract AS Overrun,
            CAST(c.Actual_Cost / con.Revised_Contract * 100 AS decimal(10,1)) AS Pct_Spent
        FROM contracts con
        JOIN costs c ON c.Job_Number = con.Job_Number
        JOIN dbo.JC_JOB_MASTER_MC j ON LTRIM(RTRIM(j.Job_Number)) = con.Job_Number AND j.Company_Code = '{CO}'
        WHERE con.Revised_Contract >= 10000
          AND c.Actual_Cost > con.Revised_Contract * 1.10
        ORDER BY c.Actual_Cost - con.Revised_Contract DESC
    """)
    out: list[Insight] = []
    for r in rows:
        pct = float(r["Pct_Spent"])
        sev = "critical" if pct >= 150 else "high" if pct >= 120 else "medium"
        co_note = (
            f" (incl ${r['Change_Order_Total']:,.0f} in change orders)"
            if r["Change_Order_Total"] else ""
        )
        out.append({
            "id": f"overbudget:{r['Job_Number']}",
            "rule": "over_budget",
            "severity": sev,
            "title": f"{r['Job_Description']} at {pct}% of revised contract",
            "detail": (
                f"Revised contract ${r['Revised_Contract']:,.0f}{co_note}, "
                f"actual cost ${r['Actual_Cost']:,.0f}, "
                f"overrun ${r['Overrun']:,.0f}."
            ),
            "job_number": r["Job_Number"],
            "amount": float(r["Overrun"]),
        })
    return out


def rule_stale_ar() -> list[Insight]:
    """Customers whose open balance hasn't moved in 60+ days.

    We trust CR_CUSTOMER_MASTER_MC.Balance (Spectrum's own current AR balance)
    and flag customers with material balance AND no recent payment.
    """
    rows = _many(f"""
        SELECT TOP 10
            LTRIM(RTRIM(Customer_Code)) AS Customer_Code,
            LTRIM(RTRIM(Name))          AS Customer_Name,
            Balance,
            Date_Last_Paid,
            Date_Last_Billed,
            DATEDIFF(day, Date_Last_Paid, GETDATE()) AS Days_Since_Paid
        FROM dbo.CR_CUSTOMER_MASTER_MC
        WHERE Company_Code = '{CO}'
          AND Balance >= 5000
          AND (Date_Last_Paid IS NULL OR Date_Last_Paid <= DATEADD(day, -60, GETDATE()))
        ORDER BY Balance DESC
    """)
    out: list[Insight] = []
    for r in rows:
        days = r.get("Days_Since_Paid")
        sev = "critical" if not days or days >= 120 else "high" if days >= 90 else "medium"
        last_paid = str(r["Date_Last_Paid"])[:10] if r["Date_Last_Paid"] else "never"
        out.append({
            "id": f"stalear:{r['Customer_Code']}",
            "rule": "stale_ar",
            "severity": sev,
            "title": f"${r['Balance']:,.0f} open from {r['Customer_Name'] or r['Customer_Code']}",
            "detail": f"Last payment {last_paid}" + (f" ({days}d ago)" if days else "") + ". Balance hasn't moved — follow up.",
            "customer_code": r["Customer_Code"],
            "amount": float(r["Balance"]),
        })
    return out


def rule_duplicate_ap() -> list[Insight]:
    """Strict duplicate detection: same vendor + amount + SAME DAY.

    We deliberately tighten from 'same month' to 'same day' because many
    legitimate recurring charges (credit cards, utilities, insurance) hit
    monthly for the same amount. Same vendor + same amount + same day is a
    much stronger duplicate signal — almost always an entry error.

    Also skip vendors whose name/code suggests a recurring service.
    """
    rows = _many(f"""
        SELECT TOP 15
            LTRIM(RTRIM(h.Vendor_Code)) AS Vendor_Code,
            LTRIM(RTRIM(h.Vendor_Name)) AS Vendor_Name,
            h.Invoice_Amount,
            CAST(h.Check_Date AS date) AS Day,
            COUNT(*) AS N,
            MIN(h.Invoice_Number) AS First_Inv,
            MAX(h.Invoice_Number) AS Last_Inv
        FROM dbo.VN_GL_DISTRIBUTION_HEADER_MC h
        WHERE h.Company_Code = '{CO}'
          AND h.Invoice_Amount >= 500
          AND h.Check_Date >= DATEADD(day, -180, GETDATE())
          -- Filter out obvious recurring vendors (credit cards, card processors)
          AND UPPER(h.Vendor_Code)    NOT IN ('CAPONE','USBCC','AMEX','CHASE','USBANK','WELLS')
          AND UPPER(h.Vendor_Name) NOT LIKE '%CREDIT CARD%'
          AND UPPER(h.Vendor_Name) NOT LIKE '%CAPITAL ONE%'
          AND UPPER(h.Vendor_Name) NOT LIKE '%US BANK%'
        GROUP BY h.Vendor_Code, h.Vendor_Name, h.Invoice_Amount, CAST(h.Check_Date AS date)
        HAVING COUNT(*) >= 2
        ORDER BY h.Invoice_Amount DESC
    """)
    out: list[Insight] = []
    for r in rows:
        amt = float(r["Invoice_Amount"])
        sev = "critical" if amt >= 10000 else "high" if amt >= 2000 else "medium"
        day = str(r["Day"])[:10]
        name = r["Vendor_Name"] or r["Vendor_Code"]
        out.append({
            "id": f"dupap:{r['Vendor_Code']}:{r['Invoice_Amount']}:{day}",
            "rule": "duplicate_ap",
            "severity": sev,
            "title": f"Duplicate AP: {name} ${amt:,.0f} posted {r['N']}x on {day}",
            "detail": (
                f"Invoices {str(r['First_Inv']).strip()} through "
                f"{str(r['Last_Inv']).strip()} — same vendor, same amount, same day. "
                "Very likely a duplicate entry."
            ),
            "vendor_code": r["Vendor_Code"],
            "amount": amt,
            "count": int(r["N"]),
        })
    return out


def rule_idle_active_jobs() -> list[Insight]:
    """Active jobs with no cost activity in 45+ days."""
    rows = _many(f"""
        WITH last_cost AS (
            SELECT LTRIM(RTRIM(Job_Number)) AS Job_Number,
                   MAX(TRY_CONVERT(date, Tran_Date_Text, 112)) AS Last_Cost_Date
            FROM dbo.JC_TRANSACTION_HISTORY_MC
            WHERE Company_Code = '{CO}'
            GROUP BY LTRIM(RTRIM(Job_Number))
        )
        SELECT TOP 10
            LTRIM(RTRIM(j.Job_Number))      AS Job_Number,
            LTRIM(RTRIM(j.Job_Description)) AS Job_Description,
            j.Original_Contract,
            lc.Last_Cost_Date,
            DATEDIFF(day, lc.Last_Cost_Date, GETDATE()) AS Days_Idle
        FROM dbo.JC_JOB_MASTER_MC j
        LEFT JOIN last_cost lc ON lc.Job_Number = LTRIM(RTRIM(j.Job_Number))
        WHERE j.Company_Code = '{CO}'
          AND j.Status_Code = 'A'
          AND j.Original_Contract >= 50000
          AND (lc.Last_Cost_Date IS NULL OR lc.Last_Cost_Date <= DATEADD(day, -45, GETDATE()))
        ORDER BY Days_Idle DESC
    """)
    out: list[Insight] = []
    for r in rows:
        days = r.get("Days_Idle")
        sev = "low" if days and days < 90 else "medium"
        out.append({
            "id": f"idle:{r['Job_Number']}",
            "rule": "idle_job",
            "severity": sev,
            "title": f"{r['Job_Description']} idle {days or 'ever'}d",
            "detail": f"No cost activity since {str(r['Last_Cost_Date'])[:10] if r['Last_Cost_Date'] else 'ever'}. Is this job actually still going? Consider closing or kicking off.",
            "job_number": r["Job_Number"],
        })
    return out


RULES = [rule_over_budget, rule_stale_ar, rule_duplicate_ap, rule_idle_active_jobs]


# --- Public ---------------------------------------------------------------

def scan() -> dict[str, Any]:
    all_insights: list[Insight] = []
    for rule in RULES:
        try:
            all_insights.extend(rule())
        except Exception as e:
            all_insights.append({
                "id": f"error:{rule.__name__}",
                "rule": rule.__name__,
                "severity": "low",
                "title": f"Rule error in {rule.__name__}",
                "detail": str(e)[:300],
            })

    # Sort: critical > high > medium > low, then by amount desc
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_insights.sort(key=lambda i: (order.get(i.get("severity", "low"), 4), -float(i.get("amount") or 0)))

    counts = {s: 0 for s in ("critical", "high", "medium", "low")}
    for ins in all_insights:
        counts[ins.get("severity", "low")] += 1

    return {"insights": all_insights, "counts": counts}


def briefing() -> str:
    data = scan()
    if not data["insights"]:
        return "No anomalies worth flagging this morning. Ship it."
    trimmed = [{k: v for k, v in i.items() if k != "id"} for i in data["insights"][:15]]
    prompt = (
        "You are writing a 60-second morning briefing for a construction company owner. "
        "Read the flagged insights below and write a prioritized summary: start with "
        "the single most important thing they should act on today, then 2-3 other items. "
        "Total 4-6 sentences. Specific names and dollar amounts. No headers, no bullets.\n\n"
        f"INSIGHTS:\n{trimmed}"
    )
    if settings.llm_provider == "ollama":
        return ai._ollama_summarize(prompt)
    return ai._anthropic_summarize(prompt)
