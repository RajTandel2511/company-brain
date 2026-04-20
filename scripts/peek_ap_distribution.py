"""Inspect how an AP invoice is split across jobs/phases/cost types."""
import os
from pathlib import Path
import pyodbc
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={os.environ['SPECTRUM_SQL_HOST']},1433;"
    f"DATABASE={os.environ['SPECTRUM_SQL_DATABASE']};"
    f"UID={os.environ['SPECTRUM_SQL_USER']};PWD={os.environ['SPECTRUM_SQL_PASSWORD']};"
    "Encrypt=yes;TrustServerCertificate=yes;ApplicationIntent=ReadOnly;",
    timeout=10, readonly=True,
)
cur = conn.cursor()

print("=== 1) Invoices on job 19.50 — header totals vs detail attribution ===")
cur.execute("""
    SELECT TOP 10
        h.Vendor_Code,
        LTRIM(RTRIM(h.Vendor_Name)) AS Vendor_Name,
        h.Invoice_Number,
        h.Invoice_Amount            AS Header_Total,
        SUM(d.Debit_Amount)         AS Total_Debits,
        SUM(d.Credit_Amount)        AS Total_Credits,
        SUM(CASE WHEN LTRIM(RTRIM(d.Job_Number)) = '19.50'
                 THEN d.Debit_Amount - d.Credit_Amount ELSE 0 END) AS Job_1950_Share,
        COUNT(DISTINCT d.Job_Number) AS Jobs_Hit,
        COUNT(*) AS Detail_Lines
    FROM dbo.VN_GL_DISTRIBUTION_HEADER_MC h
    JOIN dbo.VN_GL_DISTRIBUTION_DETAIL_MC d
      ON d.Company_Code = h.Company_Code
     AND d.Vendor_Code  = h.Vendor_Code
     AND d.Invoice_Number = h.Invoice_Number
     AND d.Invoice_Type_Code = h.Invoice_Type_Code
    WHERE h.Company_Code = 'AA1'
      AND EXISTS (
        SELECT 1 FROM dbo.VN_GL_DISTRIBUTION_DETAIL_MC dd
        WHERE dd.Company_Code = h.Company_Code
          AND dd.Vendor_Code = h.Vendor_Code
          AND dd.Invoice_Number = h.Invoice_Number
          AND dd.Invoice_Type_Code = h.Invoice_Type_Code
          AND LTRIM(RTRIM(dd.Job_Number)) = '19.50'
      )
    GROUP BY h.Vendor_Code, h.Vendor_Name, h.Invoice_Number, h.Invoice_Amount
    ORDER BY Detail_Lines DESC
""")
for row in cur.fetchall():
    print(f"  vendor={row.Vendor_Code:<10} inv={str(row.Invoice_Number)[:20]:<22} "
          f"header=${row.Header_Total:>10,.2f}  job19.50=${row.Job_1950_Share:>10,.2f}  "
          f"jobs_hit={row.Jobs_Hit}  lines={row.Detail_Lines}  "
          f"vendor={row.Vendor_Name[:30]}")

print("\n=== 2) Detail lines for one of those invoices ===")
cur.execute("""
    SELECT TOP 30
        LTRIM(RTRIM(Vendor_Code))  AS V,
        Invoice_Number             AS Inv,
        LTRIM(RTRIM(Job_Number))   AS Job,
        LTRIM(RTRIM(Phase_Code))   AS Phase,
        Cost_Type,
        Debit_Amount - Credit_Amount AS Amount,
        Remarks,
        Item_Desc
    FROM dbo.VN_GL_DISTRIBUTION_DETAIL_MC
    WHERE Company_Code = 'AA1'
      AND Vendor_Code = (
        SELECT TOP 1 h.Vendor_Code
        FROM dbo.VN_GL_DISTRIBUTION_HEADER_MC h
        JOIN dbo.VN_GL_DISTRIBUTION_DETAIL_MC d
          ON d.Company_Code = h.Company_Code AND d.Vendor_Code = h.Vendor_Code
         AND d.Invoice_Number = h.Invoice_Number AND d.Invoice_Type_Code = h.Invoice_Type_Code
        WHERE h.Company_Code = 'AA1' AND LTRIM(RTRIM(d.Job_Number)) = '19.50'
        GROUP BY h.Vendor_Code, h.Invoice_Number HAVING COUNT(DISTINCT d.Job_Number) >= 2
      )
    ORDER BY Invoice_Number
""")
for row in cur.fetchall():
    print(f"  v={row.V:<10} inv={str(row.Inv)[:18]:<20} job={row.Job:<8} phase={row.Phase:<12} "
          f"ct={str(row.Cost_Type)[:3]:<3}  ${row.Amount:>8.2f}  {str(row.Remarks)[:40]}")

print("\n=== 3) Are employees set up as vendors? ===")
cur.execute("""
    SELECT TOP 10
        LTRIM(RTRIM(v.Vendor_Code)) AS V_Code,
        LTRIM(RTRIM(v.Vendor_Name)) AS V_Name,
        LTRIM(RTRIM(v.Type))        AS V_Type,
        LTRIM(RTRIM(e.Employee_Code)) AS Emp_Code,
        LTRIM(RTRIM(e.Last_Name)) + ', ' + LTRIM(RTRIM(e.First_Name)) AS Emp_Name
    FROM dbo.VN_VENDOR_MASTER_MC v
    LEFT JOIN dbo.PR_EMPLOYEE_MASTER_1_MC e
      ON e.Company_Code = v.Company_Code
     AND (UPPER(LTRIM(RTRIM(e.Last_Name))) = UPPER(LTRIM(RTRIM(v.Vendor_Name)))
          OR UPPER(v.Vendor_Code) = UPPER(e.Employee_Code))
    WHERE v.Company_Code = 'AA1' AND e.Employee_Code IS NOT NULL
""")
for row in cur.fetchall():
    print(f"  {row.V_Code:<10} {row.V_Name[:30]:<30} type={row.V_Type:<5}  emp={row.Emp_Code} {row.Emp_Name}")

# Get vendor type distribution
print("\n=== 4) Vendor types (to spot employee/expense types) ===")
cur.execute("""
    SELECT LTRIM(RTRIM(Type)) AS T, COUNT(*) AS N
    FROM dbo.VN_VENDOR_MASTER_MC WHERE Company_Code='AA1'
    GROUP BY Type ORDER BY N DESC
""")
for row in cur.fetchall():
    print(f"  type={row.T:<8} count={row.N}")
