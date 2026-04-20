"""Hard-earned Spectrum conventions, baked into every AI prompt.

This is the difference between generic SQL and queries that actually work
against Trimble Spectrum by Viewpoint (Dexter+Chaney heritage).
"""

CONVENTIONS = """
SPECTRUM (TRIMBLE / VIEWPOINT) CONVENTIONS — CRITICAL:

1. MULTI-COMPANY. Everything lives in multi-company tables suffixed `_MC`.
   IGNORE non-_MC legacy tables entirely (they're empty or stale).
   ALWAYS filter by `Company_Code = '{COMPANY_CODE}'` unless the user asks otherwise.

2. STATUS CODES on `JC_JOB_MASTER_MC.Status_Code`:
   'A' = Active (open), 'C' = Closed, 'I' = Inactive.
   Use 'A' for "open jobs" / "current jobs" / "in progress".

3. KEY BUSINESS TABLES (prefer these):
   Jobs & phases:
     - dbo.JC_JOB_MASTER_MC       (Job_Number, Job_Description, Status_Code,
                                    Original_Contract, Start_Date, Complete_Date,
                                    Customer_Code, Project_Manager, Superintendent,
                                    Estimator, City, State)
     - dbo.JC_PHASE_MASTER_MC     (Job_Number, Phase_Code, Cost_Type, Description,
                                    Status_Code, Original_Est_Cost, Original_Est_Hours,
                                    Start_Date, End_Date)
     - dbo.JC_PHASE_SUMMARY_MC    (summary by phase)
     - dbo.JC_PROJ_COST_HISTORY_MC (projected cost updates over time)
     - dbo.JC_TRANSACTION_HISTORY_MC (every cost transaction posted to a job —
                                    Tran_Amount, Tran_Type_Code, Tran_Date_Text,
                                    Total_Hours, Employee_Name, Vendor_Name)

   AR / Billing / Customers:
     - dbo.CR_CUSTOMER_MASTER_MC  (Customer_Code, Name, Balance, Credit_Limit,
                                    Billed_YTD, Paid_YTD, Date_Last_Billed)
     - dbo.CR_INVOICE_HEADER_MC   (one row per invoice — Invoice_Or_Transaction,
                                    Invoice_Date, Invoice_Extension = invoice total,
                                    Retention_Amount, Customer_Code, Job_Number)
     - dbo.CR_INVOICE_DETAIL_MC   (invoice line items)
     - dbo.CR_BILLING_HEADER_MC   (AIA / progress billing apps — Application_Number,
                                    Revised_Contract_Amount, Complete_To_Date,
                                    Amount_Due, Retention_Amount)

   AP / Vendors / POs / Subs:
     - dbo.VN_VENDOR_MASTER_MC                (Vendor_Code, Vendor_Name, Balance,
                                                Date_Last_Invoice, Date_Last_Payment)
     - dbo.VN_GL_DISTRIBUTION_HEADER_MC       (AP invoice header — Invoice_Number,
                                                Invoice_Amount, Check_Number, Check_Date,
                                                Job_Number via Subcontract_Job, Status)
     - dbo.VN_GL_DISTRIBUTION_DETAIL_MC       (AP invoice distribution by Job_Number,
                                                Phase_Code, Cost_Type)
     - dbo.VN_PAYMENT_HISTORY_MC              (payments)
     - dbo.PO_PURCHASE_ORDER_HEADER_MC        (PO_Number, Vendor_Code, Job_Number)
     - dbo.PO_PURCHASE_ORDER_DETAIL_MC        (line items)
     - dbo.VN_SUBCONTRACT_MC                  (subcontracts)

   Payroll / HR:
     - dbo.PR_EMPLOYEE_MASTER_1_MC            (employees)
     - dbo.PR_TIME_CARD_HISTORY_MC            (labor on jobs — Employee_Code, Hours,
                                                Pay_Extension, Job_Number, Phase_Code,
                                                Work_Date, Check_Date)

   Equipment:
     - dbo.EC_EQUIPMENT_MASTER_MC             (fleet)
     - dbo.EC_METER_HISTORY_MC                (meter reads)

   Document imaging (links files stored in the Spectrum DI system):
     - dbo.DI_MASTER_MC       (Cabinet, Drawer, Folder, Reference, Keywords)
     - dbo.DI_IMAGE_XREF      (cross-references to image rows)

4. KEY COLUMN CONVENTIONS:
   - All identifier columns are varchar: Job_Number varchar(10), Phase_Code varchar(20),
     Cost_Type varchar(3), Customer_Code varchar(10), Vendor_Code varchar(10),
     Employee_Code varchar(11), Company_Code varchar(3).
   - Dates: mostly `datetime` (use >= / <) BUT some history tables store a TEXT date as
     `Tran_Date_Text varchar(8)` in YYYYMMDD format — convert with TRY_CONVERT(date, Tran_Date_Text, 112).
   - Money columns are `decimal` (trust them as currency).
   - Fiscal year/period live as `Year varchar(4)` and `GL_Period varchar(2)` on GL tables.

5. STYLE RULES:
   - Single SELECT with TOP N, no trailing semicolon.
   - Always filter by Company_Code.
   - For "over budget", compare Original_Contract vs actuals from JC_TRANSACTION_HISTORY_MC
     (SUM Tran_Amount where Tran_Type_Code means "cost") or use JC_PROJ_COST_HISTORY_MC.
   - For "AR aging", use CR_INVOICE_HEADER_MC (Invoice_Extension - Paid so far). There's
     no built-in aging view — you'll need to join with payments or compute DATEDIFF from
     Invoice_Date to GETDATE().
   - Project_Manager / Estimator / Superintendent on JC_JOB_MASTER_MC are short codes
     (varchar 15), not people's names — display them as-is.
"""


def render(company_code: str) -> str:
    return CONVENTIONS.replace("{COMPANY_CODE}", company_code)
