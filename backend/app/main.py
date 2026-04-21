from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import ai, di, docintel, files, insights, jobs, money, nas_index, rag
from .config import settings
from .db import describe_table, list_tables, run_query, UnsafeSQLError

app = FastAPI(title="Company Brain", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/schema/tables")
def schema_tables():
    return list_tables()


@app.get("/api/schema/columns")
def schema_columns(schema: str, table: str):
    return describe_table(schema, table)


class QueryIn(BaseModel):
    sql: str


@app.post("/api/query")
def query(body: QueryIn):
    try:
        return run_query(body.sql)
    except UnsafeSQLError as e:
        raise HTTPException(400, str(e))


class AskIn(BaseModel):
    question: str


@app.post("/api/ask")
def ask(body: AskIn):
    return ai.answer_question(body.question)


@app.get("/api/files/list")
def files_list(path: str = ""):
    return files.list_dir(path)


@app.get("/api/files/search")
def files_search(q: str = Query(..., min_length=1)):
    return files.search(q)


@app.get("/api/files/job/{job_number}")
def files_for_job(job_number: str):
    """Return the NAS folder and contents matching a Spectrum Job_Number."""
    folder = files.find_job_folder(job_number)
    if not folder:
        return {"job_number": job_number, "folder": None, "entries": []}
    return {
        "job_number": job_number,
        "folder": folder,
        "entries": files.list_dir(folder),
    }


@app.post("/api/files/reindex")
def files_reindex():
    files.invalidate_job_index()
    return nas_index.rebuild()


@app.get("/api/files/index-stats")
def files_index_stats():
    return nas_index.stats()


@app.get("/api/files/related")
def files_related(job: str | None = None, vendor: str | None = None,
                  customer: str | None = None, invoice: str | None = None):
    """Find NAS files that mention a given Spectrum entity."""
    if job:      return nas_index.find_related("job", job)
    if vendor:   return nas_index.find_related("vendor", vendor.upper())
    if customer: return nas_index.find_related("customer", customer.upper())
    if invoice:  return nas_index.find_related("invoice", invoice)
    raise HTTPException(400, "Provide one of: job, vendor, customer, invoice")


# --- Job Command Center ---------------------------------------------------

@app.get("/api/jobs/at-risk")
def jobs_at_risk(limit: int = 20):
    return jobs.at_risk(limit)


@app.get("/api/jobs/{job_number}")
def job_detail(job_number: str):
    return jobs.summary(job_number)


class NarrativeIn(BaseModel):
    job_number: str


@app.get("/api/di/job/{job_number}")
def di_job(job_number: str):
    return di.for_job(job_number)


@app.get("/api/di/vendor/{vendor_code}")
def di_vendor(vendor_code: str):
    return di.for_vendor(vendor_code)


@app.get("/api/di/customer/{customer_code}")
def di_customer(customer_code: str):
    return di.for_customer(customer_code)


@app.get("/api/di/search")
def di_search(q: str):
    return di.search_filenames(q)


# --- Follow the money ---------------------------------------------------

@app.get("/api/money/invoice/{vendor_code}/{invoice_number}")
def money_invoice(vendor_code: str, invoice_number: str):
    return money.invoice_trace(vendor_code, invoice_number)


@app.get("/api/money/vendor/{vendor_code}")
def money_vendor(vendor_code: str, days: int = 365):
    return money.vendor_spend(vendor_code, days=days)


@app.get("/api/money/vendors")
def money_vendor_list(search: str = "", employees_only: bool = False, limit: int = 100):
    return money.list_vendors(search=search, employees_only=employees_only, limit=limit)


# --- Document intelligence ----
@app.get("/api/docintel/stats")
def docintel_stats():
    return docintel.stats()


@app.post("/api/docintel/run")
def docintel_run(batch: int = 500):
    return docintel.run(batch_limit=batch)


@app.get("/api/docintel/files")
def docintel_files(entity_type: str, entity_value: str, limit: int = 200):
    """All NAS files whose CONTENT mentions a given entity."""
    return docintel.files_for_entity(entity_type, entity_value, limit)


@app.get("/api/docintel/search")
def docintel_search(q: str, limit: int = 50):
    """Full-text search across extracted file content."""
    c = docintel._connect()
    rows = c.execute("""
        SELECT f.path, f.name, f.size, f.modified, length(fc.text) AS clen
        FROM file_content fc
        JOIN files f ON f.id = fc.file_id
        WHERE fc.text LIKE ?
        ORDER BY f.modified DESC
        LIMIT ?
    """, (f"%{q}%", limit)).fetchall()
    c.close()
    return [
        {"path": r[0], "name": r[1], "size": r[2], "modified": r[3], "text_length": r[4]}
        for r in rows
    ]


@app.get("/api/rag/stats")
def rag_stats():
    return rag.stats()


@app.get("/api/rag/search")
def rag_search(q: str, limit: int = 10):
    """Semantic search over indexed NAS document chunks."""
    return {"query": q, "results": rag.search(q, limit=limit)}


@app.get("/api/insights")
def insights_scan():
    return insights.scan()


@app.get("/api/insights/briefing")
def insights_briefing():
    return {"briefing": insights.briefing()}


@app.post("/api/jobs/{job_number}/narrative")
def job_narrative(job_number: str):
    s = jobs.summary(job_number)
    if not s.get("found"):
        raise HTTPException(404, "Job not found")
    prompt = (
        "You are writing a 'state of the job' briefing for a construction executive. "
        "Base it only on the data below. Keep it to 3-4 sentences. Highlight the "
        "most actionable thing: cost overrun, labor burn, billing stale, RFIs aging, "
        "unusual AP activity. No fluff. Use dollar amounts rounded to thousands.\n\n"
        f"DATA:\n{s}"
    )
    text = ai._anthropic_summarize(prompt) if settings.llm_provider == "anthropic" else ai._ollama_summarize(prompt)
    return {"job_number": job_number, "narrative": text}


@app.get("/api/files/get")
def files_get(path: str):
    try:
        p, gen = files.stream_file(path)
    except FileNotFoundError:
        raise HTTPException(404, "Not found")
    except PermissionError:
        raise HTTPException(403, "Forbidden")
    import mimetypes
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    return StreamingResponse(gen, media_type=mime, headers={
        "Content-Disposition": f'inline; filename="{p.name}"'
    })


# --- Dashboard: curated Spectrum queries tuned for the AA1 multi-company schema --
def _q(sql: str) -> str:
    """Interpolate the configured company code into a query template."""
    return sql.replace("{CO}", settings.spectrum_company_code)


DASHBOARD_QUERIES = {
    "active_jobs": _q("""
        SELECT TOP 50
            LTRIM(RTRIM(Job_Number))       AS Job_Number,
            LTRIM(RTRIM(Job_Description))  AS Job_Description,
            LTRIM(RTRIM(Customer_Code))    AS Customer_Code,
            LTRIM(RTRIM(Project_Manager))  AS Project_Manager,
            LTRIM(RTRIM(Superintendent))   AS Superintendent,
            LTRIM(RTRIM(City)) + ', ' + LTRIM(RTRIM(State)) AS Location,
            Original_Contract,
            Start_Date,
            Est_Complete_Date
        FROM dbo.JC_JOB_MASTER_MC
        WHERE Company_Code = '{CO}' AND Status_Code = 'A'
        ORDER BY Original_Contract DESC
    """),

    "ar_aging": _q("""
        WITH inv AS (
            SELECT
                h.Customer_Code,
                h.Invoice_Or_Transaction AS Invoice_Number,
                h.Job_Number,
                h.Invoice_Date,
                h.Invoice_Extension AS Invoice_Amount,
                h.Retention_Amount,
                DATEDIFF(day, h.Invoice_Date, GETDATE()) AS Age_Days
            FROM dbo.CR_INVOICE_HEADER_MC h
            WHERE h.Company_Code = '{CO}'
              AND h.Invoice_Date >= DATEADD(year, -2, GETDATE())
              AND h.Invoice_Extension > 0
        )
        SELECT TOP 100
            inv.Customer_Code,
            c.Name AS Customer_Name,
            inv.Invoice_Number,
            inv.Job_Number,
            inv.Invoice_Date,
            inv.Invoice_Amount,
            inv.Retention_Amount,
            inv.Age_Days,
            CASE
                WHEN inv.Age_Days <= 30 THEN '0-30'
                WHEN inv.Age_Days <= 60 THEN '31-60'
                WHEN inv.Age_Days <= 90 THEN '61-90'
                ELSE '90+'
            END AS Bucket
        FROM inv
        LEFT JOIN dbo.CR_CUSTOMER_MASTER_MC c
            ON c.Company_Code = '{CO}' AND c.Customer_Code = inv.Customer_Code
        ORDER BY inv.Age_Days DESC
    """),

    "top_customers_ytd": _q("""
        -- Computed from invoice history (Billed_YTD on master isn't reliable here)
        WITH ytd AS (
            SELECT
                Customer_Code,
                SUM(Invoice_Extension) AS Billed_YTD,
                COUNT(*) AS Invoice_Count
            FROM dbo.CR_INVOICE_HEADER_MC
            WHERE Company_Code = '{CO}'
              AND Invoice_Date >= DATEFROMPARTS(YEAR(GETDATE()), 1, 1)
            GROUP BY Customer_Code
        )
        SELECT TOP 20
            LTRIM(RTRIM(y.Customer_Code)) AS Customer_Code,
            LTRIM(RTRIM(c.Name))          AS Customer_Name,
            y.Billed_YTD,
            y.Invoice_Count,
            c.Balance,
            c.Credit_Limit,
            c.Date_Last_Billed
        FROM ytd y
        LEFT JOIN dbo.CR_CUSTOMER_MASTER_MC c
            ON c.Company_Code = '{CO}' AND c.Customer_Code = y.Customer_Code
        ORDER BY y.Billed_YTD DESC
    """),

    "top_vendors_ytd": _q("""
        SELECT TOP 20
            v.Vendor_Code,
            v.Vendor_Name,
            v.Balance,
            v.Date_Last_Invoice,
            v.Date_Last_Payment,
            SUM(p.Payment_Amount) AS Paid_YTD
        FROM dbo.VN_VENDOR_MASTER_MC v
        LEFT JOIN dbo.VN_PAYMENT_HISTORY_MC p
            ON p.Company_Code = v.Company_Code
           AND p.Vendor_Code = v.Vendor_Code
           AND p.Check_Date >= DATEFROMPARTS(YEAR(GETDATE()), 1, 1)
        WHERE v.Company_Code = '{CO}'
        GROUP BY v.Vendor_Code, v.Vendor_Name, v.Balance, v.Date_Last_Invoice, v.Date_Last_Payment
        ORDER BY ISNULL(SUM(p.Payment_Amount), 0) DESC
    """),

    "jobs_over_budget": _q("""
        WITH costs AS (
            SELECT Job_Number, SUM(Tran_Amount) AS Actual_Cost
            FROM dbo.JC_TRANSACTION_HISTORY_MC
            WHERE Company_Code = '{CO}'
            GROUP BY Job_Number
        )
        SELECT TOP 30
            j.Job_Number,
            j.Job_Description,
            j.Status_Code,
            j.Original_Contract,
            c.Actual_Cost,
            j.Original_Contract - ISNULL(c.Actual_Cost, 0) AS Gross_Variance,
            CASE WHEN j.Original_Contract > 0
                 THEN CAST(ISNULL(c.Actual_Cost, 0) / j.Original_Contract * 100 AS decimal(10,1))
                 ELSE 0 END AS Pct_of_Contract
        FROM dbo.JC_JOB_MASTER_MC j
        LEFT JOIN costs c ON c.Job_Number = j.Job_Number
        WHERE j.Company_Code = '{CO}' AND j.Status_Code = 'A' AND j.Original_Contract > 0
        ORDER BY Pct_of_Contract DESC
    """),

    "recent_billings": _q("""
        SELECT TOP 30
            b.Job_Number,
            j.Job_Description,
            b.Customer_Code,
            b.Application_Number,
            b.Period_End_Date,
            b.Revised_Contract_Amount,
            b.Complete_To_Date,
            b.Amount_Due,
            b.Retention_Amount
        FROM dbo.CR_BILLING_HEADER_MC b
        LEFT JOIN dbo.JC_JOB_MASTER_MC j
            ON j.Company_Code = b.Company_Code AND j.Job_Number = b.Job_Number
        WHERE b.Company_Code = '{CO}'
          AND b.Period_End_Date >= DATEADD(day, -90, GETDATE())
        ORDER BY b.Period_End_Date DESC
    """),

    "open_pos": _q("""
        SELECT TOP 30
            h.PO_Number,
            h.Vendor_Code,
            v.Vendor_Name,
            h.Job_Number,
            h.PO_Date_List1 AS PO_Date,
            SUM(d.Line_Extension_List1) AS PO_Total,
            SUM(d.Received_Extension) AS Received_Total
        FROM dbo.PO_PURCHASE_ORDER_HEADER_MC h
        LEFT JOIN dbo.PO_PURCHASE_ORDER_DETAIL_MC d
            ON d.Company_Code = h.Company_Code AND d.PO_Number = h.PO_Number
        LEFT JOIN dbo.VN_VENDOR_MASTER_MC v
            ON v.Company_Code = h.Company_Code AND v.Vendor_Code = h.Vendor_Code
        WHERE h.Company_Code = '{CO}'
        GROUP BY h.PO_Number, h.Vendor_Code, v.Vendor_Name, h.Job_Number, h.PO_Date_List1
        ORDER BY h.PO_Date_List1 DESC
    """),
}


@app.get("/api/dashboard/{key}")
def dashboard(key: str):
    sql = DASHBOARD_QUERIES.get(key)
    if not sql:
        raise HTTPException(404, "Unknown dashboard key")
    try:
        return run_query(sql)
    except Exception as e:
        raise HTTPException(500, f"Query failed: {e}")


@app.get("/api/dashboard")
def dashboard_list():
    return [{"key": k, "title": k.replace("_", " ").title()} for k in DASHBOARD_QUERIES]
