# Spectrum schema snapshot — Spectrum_0014100000QHkIIAA1 @ allairmechanical-data.dexterchaney.com

**Total objects:** 6130


## Top 50 tables by row count

| schema | table | rows |
|---|---|---:|
| dbo | AuditLogDetail | 2,465,970 |
| dbo | AuditLog | 593,975 |
| dbo | PA_EVENT_LOG | 252,598 |
| dbo | MSchange_tracking_history | 190,410 |
| dbo | PA_COLUMN_NAMES | 169,407 |
| dbo | JC_TRANSACTION_HISTORY_MC | 153,558 |
| dbo | PR_GL_HISTORY_MC | 136,755 |
| dbo | GL_DETAIL_MC | 104,047 |
| dbo | PR_TIME_CARD_HISTORY_MC | 81,623 |
| dbo | DI_JC_HISTORY_XREF_MC | 76,929 |
| dbo | VN_GL_HISTORY_MC | 76,263 |
| dbo | Z_SpectrumLicenseUsageInfo | 75,707 |
| dbo | VN_GL_DISTRIBUTION_DETAIL_MC | 58,614 |
| dbo | PA_DATA_TABLE_FUNCTION_XREF | 55,430 |
| dbo | PA_DATA_FUNCTION_LINKS | 42,722 |
| dbo | JC_PROJ_COST_HISTORY_MC | 42,567 |
| dbo | DI_MASTER_MC | 35,422 |
| dbo | VN_ROUTING_HISTORY_MC | 35,355 |
| dbo | PR_TC_DET_UNION_FRI_HIST_MC | 34,102 |
| dbo | PR_EMPL_TAX_HIST_EXEMPT_ADJ_MC | 31,147 |
| dbo | PA_DATA_LX_LEXICONSTRINGS | 27,434 |
| dbo | CR_GL_HISTORY_MC | 25,280 |
| dbo | EM_TEMP_COPY_COMP_COLUMNS | 23,931 |
| dbo | VN_PAYMENT_HISTORY_MC | 21,938 |
| dbo | VN_GL_DISTRIBUTION_HEADER_MC | 21,411 |
| dbo | PR_EMPL_STATE_TAX_HIST_MC | 20,197 |
| dbo | DI_IMAGE_MASTER | 19,318 |
| dbo | DI_IMAGE_XREF | 17,991 |
| dbo | DI_IMAGE_ANNOTATIONS | 16,852 |
| dbo | GL_DETAIL_UPDATE_LOG_MC | 16,073 |
| dbo | JC_PHASE_MASTER_MC | 15,843 |
| dbo | CR_BILL_DETAIL_MC | 15,391 |
| dbo | PR_CHECK_VOL_DED_HISTORY_MC | 14,430 |
| dbo | JC_PHASE_SUMMARY_MC | 11,308 |
| dbo | PR_EMPL_DEPT_HIST_MC | 10,800 |
| dbo | BI_CHECK_HISTORY_MC_ID | 10,097 |
| dbo | PR_CHECK_HISTORY_MC | 10,097 |
| dbo | PR_EMPL_WORK_COMP_HIST_MC | 9,954 |
| dbo | EC_ACTUAL_COST_HISTORY_MC | 9,450 |
| dbo | PR_TIME_OFF_BANK_LOG_MC | 9,266 |
| dbo | EL_SETUP_DETAIL_MC | 9,129 |
| dbo | PT_FILE_NAME_XREF_MC | 9,084 |
| dbo | BR_CHECK_RECON_MC | 6,931 |
| dbo | ST_DI_MASTER_MC_XREF | 6,702 |
| dbo | BR_AUTODEP_CHECK_XREF_MC | 6,382 |
| dbo | PA_OPR_LICENSE_TYPE_CONTRACTED | 6,030 |
| dbo | PR_CHECK_AUTO_DEP_ALLOC_HIST_MC | 5,966 |
| dbo | BR_CHECK_RECON_HISTORY_MC | 5,961 |
| dbo | CR_INVOICE_DETAIL_MC | 5,572 |
| dbo | JC_JOB_COMPLIANCE_MC | 5,431 |

## Tables grouped by domain (substring match, case-insensitive)


### Jobs / Project  (488)

- `cdc.JC_JOB_MASTER_MC_v1_CT` — 21 rows
- `cdc.JC_PHASE_ESTIMATES_MC_v1_CT` — 0 rows
- `cdc.JC_PHASE_MASTER_MC_v1_CT` — 144 rows
- `cdc.JC_STD_PHASE_DESCRIPTION_MC_v1_CT` — 0 rows
- `cdc.VN_SUBCONTRACT_PHASE_MC_v1_CT` — 0 rows
- `dbo.AP_INVOICE_JOB_COSTS_V_MC`
- `dbo.AP_JOB_COSTS_SUMMARY_V_MC`
- `dbo.BI_DW_REBUILD_JOBS`
- `dbo.CR_JOB_CUSTOMER_XREF`
- `dbo.CR_JOB_CUSTOMER_XREF_MC`
- `dbo.CR_OPEN_ITEM_JOB_XREF`
- `dbo.CR_OPEN_ITEM_JOB_XREF_MC`
- `dbo.CR_PAY_HIST_JOB_XREF`
- `dbo.CR_PAY_HIST_JOB_XREF_MC`
- `dbo.CR_PROJECTED_REV_BY_JOB1_MC`
- `dbo.CR_PROJECTED_REV_BY_JOB2_MC`
- `dbo.CR_PROJECTED_REVENUE_BY_JOB_MC`
- `dbo.CR_TEMP_CO_COST_REP_JOB`
- `dbo.CR_TEMP_CO_COST_REP_JOB_MC` — 0 rows
- `dbo.CR_TEMP_CO_COST_REP_PHASE`
- `dbo.CR_TEMP_CO_COST_REP_PHASE_MC` — 0 rows
- `dbo.CR_TEMP_PHASE_CO_EXPT_REP`
- `dbo.CR_TEMP_PHASE_CO_EXPT_REP_MC` — 0 rows
- `dbo.CR_TEMP_STATMNT_JOB_XREF`
- `dbo.CR_TEMP_STATMNT_JOB_XREF_MC` — 2 rows
- `dbo.DI_MASTER_JOB_V`
- `dbo.EC_EQUIPMENT_RATE_BY_JOB`
- `dbo.EC_EQUIPMENT_RATE_BY_JOB_MC`
- `dbo.EC_JOB_EQUIPMENT_RATE`
- `dbo.EC_JOB_EQUIPMENT_RATE_1_MC`
- `dbo.EC_JOB_EQUIPMENT_RATE_MC` — 7 rows
- `dbo.EC_RECUR_TRAN_JOB_XREF`
- `dbo.EC_RECUR_TRAN_JOB_XREF_MC`
- `dbo.EC_TEMP_JOB_EQUIP_RATE`
- `dbo.EC_TEMP_JOB_EQUIP_RATE_MC` — 0 rows
- `dbo.EC_TRAN_JOB_XREF`
- `dbo.EC_TRAN_JOB_XREF_MC`
- `dbo.EL_COST_CODE_PHASE`
- `dbo.EL_COST_CODE_PHASE_MC` — 0 rows
- `dbo.EL_HARD_DOLLAR_PHASE_TEMP`
- `dbo.EL_HARD_DOLLAR_PHASE_TEMP_MC` — 0 rows
- `dbo.EL_STAND_COST_CODE_PHASE`
- `dbo.EL_STAND_COST_CODE_PHASE_MC` — 1 rows
- `dbo.EL_STD_CCODE_PHASE_XREF`
- `dbo.EL_STD_CCODE_PHASE_XREF_MC`
- `dbo.ET_REQ_HISTORY_SUM_JOB`
- `dbo.ET_REQ_HISTORY_SUM_JOB_MC` — 0 rows
- `dbo.HR_CREW_MNG_JOB`
- `dbo.HR_CREW_MNG_JOB_MC` — 0 rows
- `dbo.HR_JOB_GROUP_MASTER`
- `dbo.HR_JOB_GROUP_MASTER_MC` — 11 rows
- `dbo.HR_JOB_OPEN_NOTES_MASTER_MC`
- `dbo.HR_JOB_TITLE_MASTER`
- `dbo.HR_JOB_TITLE_MASTER_MC` — 15 rows
- `dbo.HR_JOB_TITLE_NOTES_MASTER_MC`
- `dbo.HR_JOB_TITLE_PAY_LEVEL`
- `dbo.HR_JOB_TITLE_PAY_LEVEL_MC` — 0 rows
- `dbo.HR_JOB_TITLE_REQUIREMENTS`
- `dbo.HR_JOB_TITLE_REQUIREMENTS_MC` — 6 rows
- `dbo.HR_OPENINGS_JOB_TITLE_XREF`

### AR / Billing  (334)

- `cdc.CR_CUSTOMER_CONTACTS_MC_v1_CT` — 7 rows
- `cdc.CR_CUSTOMER_MASTER_MC_v1_CT` — 83 rows
- `cdc.CR_INVOICE_DETAIL_MC_v1_CT` — 6 rows
- `cdc.CR_INVOICE_HEADER_MC_v1_CT` — 6 rows
- `dbo.AP_INVOICE_JOB_COSTS_V_MC`
- `dbo.AP_INVOICES_IN_PROGRESS_V_MC`
- `dbo.AR_ENTITY_INVOICE_NUMBER`
- `dbo.AR_ENTITY_INVOICE_NUMBER_MC` — 0 rows
- `dbo.CR_BILLING_HEADER`
- `dbo.CR_BILLING_HEADER_MC` — 1,462 rows
- `dbo.CR_CUSTOMER_ALPHA_XREF`
- `dbo.CR_CUSTOMER_ALPHA_XREF_MC`
- `dbo.CR_CUSTOMER_ATTRIB_V`
- `dbo.CR_CUSTOMER_BY_ID`
- `dbo.CR_CUSTOMER_CATEGORY`
- `dbo.CR_CUSTOMER_CATEGORY_MC` — 1 rows
- `dbo.CR_CUSTOMER_CHANGE_1`
- `dbo.CR_CUSTOMER_CHANGE_1_MC` — 0 rows
- `dbo.CR_CUSTOMER_CHANGE_2`
- `dbo.CR_CUSTOMER_CHANGE_2_MC` — 0 rows
- `dbo.CR_CUSTOMER_CONTACTS`
- `dbo.CR_CUSTOMER_CONTACTS_MC` — 165 rows
- `dbo.CR_CUSTOMER_CURRENCY_OVERRIDE`
- `dbo.CR_CUSTOMER_CURRENCY_OVERRIDE_MC` — 0 rows
- `dbo.CR_CUSTOMER_INFOBAR_MC`
- `dbo.CR_CUSTOMER_INQUIRY`
- `dbo.CR_CUSTOMER_MASTER`
- `dbo.CR_CUSTOMER_MASTER_2V_MC`
- `dbo.CR_CUSTOMER_MASTER_MC` — 422 rows
- `dbo.CR_CUSTOMER_MASTER1_V`
- `dbo.CR_CUSTOMER_MASTER1_V_MC`
- `dbo.CR_CUSTOMER_MASTER2_V`
- `dbo.CR_CUSTOMER_NOTES_MASTER`
- `dbo.CR_CUSTOMER_NOTES_MASTER_MC`
- `dbo.CR_CUSTOMER_RELATED_PARTY`
- `dbo.CR_CUSTOMER_RELATED_PARTY_MC` — 35 rows
- `dbo.CR_CUSTOMER_USER_FIELDS`
- `dbo.CR_CUSTOMER_USER_FIELDS_MC` — 0 rows
- `dbo.CR_CUSTOMER_WORKFLOW_MC` — 0 rows
- `dbo.CR_CUSTOMER_YTD_BILLINGS_V_MC`
- `dbo.CR_FIXED_BILLING_ITEM`
- `dbo.CR_FIXED_BILLING_ITEM_MC` — 0 rows
- `dbo.CR_HIST_INVOICE`
- `dbo.CR_HIST_INVOICE_MC` — 0 rows
- `dbo.CR_INVOICE_DETAIL`
- `dbo.CR_INVOICE_DETAIL_MC` — 5,572 rows
- `dbo.CR_INVOICE_DETAIL_V1`
- `dbo.CR_INVOICE_DETAIL_V1_MC`
- `dbo.CR_INVOICE_HEADER`
- `dbo.CR_INVOICE_HEADER_MC` — 2,914 rows
- `dbo.CR_INVOICE_HEADER1_V`
- `dbo.CR_INVOICE_LOG`
- `dbo.CR_INVOICE_LOG_MC` — 2,718 rows
- `dbo.CR_INVOICE_SPECIFIC_NOTES`
- `dbo.CR_INVOICE_SPECIFIC_NOTES_EXIST`
- `dbo.CR_INVOICE_SPECIFIC_NOTES_MC` — 22 rows
- `dbo.CR_INVOICE_TEMP`
- `dbo.CR_INVOICE_TEMP_MC` — 0 rows
- `dbo.CR_INVOICE_USER_DEF_FIELDS`
- `dbo.CR_INVOICE_USER_FIELDS`

### AP / PO / Commitments  (657)

- `cdc.JC_CM_COMMITTED_H_MC_v1_CT` — 0 rows
- `cdc.PO_BLANKET_RELEASE_HEADER_MC_v1_CT` — 0 rows
- `cdc.PO_PURCHASE_ORDER_DETAIL_MC_v1_CT` — 64 rows
- `cdc.PO_PURCHASE_ORDER_HEADER_MC_v1_CT` — 200 rows
- `cdc.VN_SUBCONTRACT_MC_v1_CT` — 0 rows
- `cdc.VN_SUBCONTRACT_PHASE_MC_v1_CT` — 0 rows
- `cdc.VN_VENDOR_COST_CENTERS_MC_v1_CT` — 0 rows
- `cdc.VN_VENDOR_CURRENCY_OVERRIDE_MC_v1_CT` — 0 rows
- `cdc.VN_VENDOR_LOCATIONS_MC_v1_CT` — 0 rows
- `cdc.VN_VENDOR_MASTER_MC_v1_CT` — 128 rows
- `dbo.AP_SUBCONTRACT_USER_FIELDS`
- `dbo.AP_SUBCONTRACT_USER_FIELDS_MC` — 0 rows
- `dbo.AP_SUBCONTRACT_USER_FIELDS_XREF`
- `dbo.AP_SUBCONTRACT_USER_FIELDS_XREF_MC` — 0 rows
- `dbo.BR_CLEARED_CKS_IMPORT_ERR`
- `dbo.BR_CLEARED_CKS_IMPORT_ERR_MC` — 0 rows
- `dbo.BR_DEPOSIT_RECON`
- `dbo.BR_DEPOSIT_RECON_HISTORY`
- `dbo.BR_DEPOSIT_RECON_HISTORY_MC` — 1,067 rows
- `dbo.BR_DEPOSIT_RECON_MC` — 788 rows
- `dbo.BR_TEMP_POSITIVE_PAY_CHECKS`
- `dbo.BR_TEMP_POSITIVE_PAY_CHECKS_MC` — 0 rows
- `dbo.CL_TEMP_REPORT_PARAMETERS` — 0 rows
- `dbo.CP_TEMP_SDI_REPORT`
- `dbo.CP_TEMP_SDI_REPORT_MC` — 0 rows
- `dbo.CP_TEMP_UNION_REPORT`
- `dbo.CP_TEMP_UNION_REPORT_MC` — 0 rows
- `dbo.CP_TEMP_WA_LI_REPORT`
- `dbo.CP_TEMP_WA_LI_REPORT_MC` — 0 rows
- `dbo.CP_TEMP_WA_LI_REPORT1_V`
- `dbo.CP_TEMP_WC_REPORT_GL_SUM`
- `dbo.CP_TEMP_WC_REPORT_GL_SUM_MC` — 0 rows
- `dbo.CR_MY_PROPOSED_CR_AGING_MC`
- `dbo.CR_MY_PROPOSED_CR_AGING_TOP_MC`
- `dbo.CR_PRE_BILL_UNPOSTED_XREF`
- `dbo.CR_PRE_BILL_UNPOSTED_XREF_MC`
- `dbo.CR_TEMP_CASH_REC_UNPOSTED`
- `dbo.CR_TEMP_CASH_REC_UNPOSTED_MC` — 0 rows
- `dbo.CR_TEMP_DRAW_REPORT`
- `dbo.CR_TEMP_DRAW_REPORT_MC` — 2 rows
- `dbo.CR_UNPOSTED_INVOICE_SEARCH`
- `dbo.CR_UNPOSTED_INVOICE_SEARCH_MC`
- `dbo.DI_ARCHIVE_REPORTS_DEFAULTS`
- `dbo.DI_ARCHIVE_REPORTS_DEFAULTS_MC` — 1 rows
- `dbo.EC_COMPONENT_CODE`
- `dbo.EC_COMPONENT_CODE_MC` — 19 rows
- `dbo.EC_COMPONENT_GROUP`
- `dbo.EC_COMPONENT_GROUP_MC` — 21 rows
- `dbo.EC_COMPONENT_LOG`
- `dbo.EC_COMPONENT_LOG_MC` — 1 rows
- `dbo.EC_COST_CATEGORY_COMPONENT_GROUP`
- `dbo.EC_COST_CATEGORY_COMPONENT_GROUP_MC`
- `dbo.EC_EQP_COMPONENT_NOTES_MASTER_MC`
- `dbo.EC_EQP_COMPONENTS`
- `dbo.EC_EQP_COMPONENTS_MC` — 37 rows
- `dbo.EC_EQP_TYPE_STD_COMPOS`
- `dbo.EC_EQP_TYPE_STD_COMPOS_MC` — 132 rows
- `dbo.EC_TEMP_CHARGEABLE_REPORT`
- `dbo.EC_TEMP_CHARGEABLE_REPORT_MC` — 0 rows
- `dbo.EC_TEMP_CT_IMPORT_TRAN`

### Payroll / HR  (347)

- `cdc.CR_PAY_ADJUST_HISTORY_MC_v1_CT` — 111 rows
- `cdc.PR_EMPLOYEE_1095C_DEP_MC_v1_CT` — 0 rows
- `cdc.PR_EMPLOYEE_1095C_MC_v1_CT` — 0 rows
- `cdc.PR_EMPLOYEE_CODE_CHANGE_HISTORY_MC_v1_CT` — 0 rows
- `cdc.PR_EMPLOYEE_MASTER_1_MC_v1_CT` — 2 rows
- `cdc.PR_EMPLOYEE_MASTER_3_MC_v1_CT` — 0 rows
- `cdc.PR_EMPLOYEE_STATUS_MC_v1_CT` — 0 rows
- `dbo.BR_ELECTRONIC_PAYMENT_SETUP`
- `dbo.BR_ELECTRONIC_PAYMENT_SETUP_CRYPTO`
- `dbo.BR_ELECTRONIC_PAYMENT_SETUP_CRYPTO_MC`
- `dbo.BR_ELECTRONIC_PAYMENT_SETUP_MC` — 13 rows
- `dbo.BR_RECON_ENTRY_DEDUCTIONS`
- `dbo.BR_RECON_ENTRY_DEDUCTIONS_MC` — 0 rows
- `dbo.BR_TEMP_POSITIVE_PAY_CHECKS`
- `dbo.BR_TEMP_POSITIVE_PAY_CHECKS_MC` — 0 rows
- `dbo.CP_TEMP_DEDUCTION_DETAIL`
- `dbo.CP_TEMP_DEDUCTION_DETAIL_MC` — 0 rows
- `dbo.CR_PAY_ADJUST_HISTORY`
- `dbo.CR_PAY_ADJUST_HISTORY_MC` — 4,029 rows
- `dbo.CR_PAY_HIST_JOB_XREF`
- `dbo.CR_PAY_HIST_JOB_XREF_MC`
- `dbo.CR_PAYMENT_HISTORY_V`
- `dbo.CR_TEMP_PAYMENT`
- `dbo.CR_TEMP_PAYMENT_MC` — 0 rows
- `dbo.EK_PAYROLL_EARNINGS_ADDON_DED_MC`
- `dbo.EK_PAYROLL_EARNINGS_GROSS_PAY_MC`
- `dbo.EK_PAYROLL_EARNINGS_SUMMARY_MC`
- `dbo.EK_PAYROLL_EARNINGS_SUMMARY_YTD_MC`
- `dbo.EK_PAYROLL_EARNINGS_TAXES_MC`
- `dbo.EK_PAYROLL_EARNINGS_TAXES_YTD_MC`
- `dbo.ET_EMPLOYEE_AUTHORIZATION`
- `dbo.ET_EMPLOYEE_AUTHORIZATION_MC` — 4 rows
- `dbo.ET_EMPLOYEE_WH_AUTH`
- `dbo.ET_EMPLOYEE_WH_AUTH_MC` — 0 rows
- `dbo.ET_EMPLOYEE_YARD_AUTH`
- `dbo.ET_EMPLOYEE_YARD_AUTH_MC` — 0 rows
- `dbo.ET_TEMP_EMPLOYEE_AUTH`
- `dbo.ET_TEMP_EMPLOYEE_AUTH_MC` — 0 rows
- `dbo.HR_EMPLOYEE_BENEFITS`
- `dbo.HR_EMPLOYEE_BENEFITS_MC` — 1,243 rows
- `dbo.HR_EMPLOYEE_BENEFITS1_V`
- `dbo.HR_EMPLOYEE_CIVIL`
- `dbo.HR_EMPLOYEE_CIVIL_MC` — 8 rows
- `dbo.HR_Employee_Civil1_V`
- `dbo.HR_EMPLOYEE_ENTITY_BENEFIT`
- `dbo.HR_EMPLOYEE_ENTITY_BENEFIT_MC` — 0 rows
- `dbo.HR_EMPLOYEE_ENTITY_BENEFIT1_V`
- `dbo.HR_EMPLOYEE_ENTITY_FMLA`
- `dbo.HR_EMPLOYEE_ENTITY_FMLA_MC` — 0 rows
- `dbo.HR_EMPLOYEE_FIELDS_V`
- `dbo.HR_EMPLOYEE_FMLA`
- `dbo.HR_EMPLOYEE_FMLA_MC` — 1 rows
- `dbo.HR_EMPLOYEE_FORMS`
- `dbo.HR_EMPLOYEE_FORMS_MC` — 856 rows
- `dbo.HR_EMPLOYEE_INSURANCE`
- `dbo.HR_EMPLOYEE_INSURANCE_MC` — 2 rows
- `dbo.HR_EMPLOYEE_LOG`
- `dbo.HR_EMPLOYEE_LOG_FIELDS_V`
- `dbo.HR_EMPLOYEE_LOG_MC` — 1,858 rows
- `dbo.HR_EMPLOYEE_LOG1_V`

### Equipment  (150)

- `cdc.EC_EQUIPMENT_MASTER_MC_v1_CT` — 0 rows
- `cdc.EC_EQUIPMENT_STATUS_MC_v1_CT` — 0 rows
- `cdc.EC_EQUIPMENT_TYPE_MC_v1_CT` — 0 rows
- `dbo.CL_TEMP_REPORT_PARAMETERS` — 0 rows
- `dbo.CR_TEMP_CASH_REC_GL_UPD_EQUIP_COSTS`
- `dbo.CR_TEMP_CASH_REC_GL_UPD_EQUIP_COSTS_MC` — 0 rows
- `dbo.EC_EQUIP_MSTR_USER_FIELDS`
- `dbo.EC_EQUIP_MSTR_USER_FIELDS_MC` — 168 rows
- `dbo.EC_EQUIP_TYPE_BUDGET_COSTS`
- `dbo.EC_EQUIP_TYPE_BUDGET_DETAIL`
- `dbo.EC_EQUIP_TYPE_BUDGET_DETAIL_MC` — 0 rows
- `dbo.EC_EQUIP_TYPE_BUDGET_HEADER`
- `dbo.EC_EQUIP_TYPE_BUDGET_HEADER_MC` — 0 rows
- `dbo.EC_EQUIPMENT_AP_ROUTE`
- `dbo.EC_EQUIPMENT_AP_ROUTE_MC` — 28 rows
- `dbo.EC_EQUIPMENT_BY_ID`
- `dbo.EC_EQUIPMENT_CHANGE_1`
- `dbo.EC_EQUIPMENT_CHANGE_1_MC` — 0 rows
- `dbo.EC_EQUIPMENT_ESS_V_MC`
- `dbo.EC_EQUIPMENT_GROUP_FILE`
- `dbo.EC_EQUIPMENT_GROUP_FILE_MC` — 2 rows
- `dbo.EC_EQUIPMENT_LAST_METER_MC`
- `dbo.EC_EQUIPMENT_MASTER`
- `dbo.EC_EQUIPMENT_MASTER_GPS`
- `dbo.EC_EQUIPMENT_MASTER_GPS_MC` — 36 rows
- `dbo.EC_EQUIPMENT_MASTER_MC` — 92 rows
- `dbo.EC_EQUIPMENT_MASTER_MC1_V`
- `dbo.EC_EQUIPMENT_MASTER3_V`
- `dbo.EC_EQUIPMENT_MASTER4_V`
- `dbo.EC_EQUIPMENT_MASTER6_V`
- `dbo.EC_EQUIPMENT_MASTER6_V_MC`
- `dbo.EC_EQUIPMENT_NOTES_MASTER_MC`
- `dbo.EC_EQUIPMENT_RATE_BY_JOB`
- `dbo.EC_EQUIPMENT_RATE_BY_JOB_MC`
- `dbo.EC_EQUIPMENT_RUN_LOG_MC` — 0 rows
- `dbo.EC_EQUIPMENT_STATUS`
- `dbo.EC_EQUIPMENT_STATUS_MC` — 33 rows
- `dbo.EC_EQUIPMENT_TYPE`
- `dbo.EC_EQUIPMENT_TYPE_MC` — 74 rows
- `dbo.EC_FIELD_METER_EXCEPTION_MC` — 0 rows
- `dbo.EC_FUEL_OIL`
- `dbo.EC_FUEL_OIL_MC` — 15 rows
- `dbo.EC_JOB_EQUIPMENT_RATE`
- `dbo.EC_JOB_EQUIPMENT_RATE_1_MC`
- `dbo.EC_JOB_EQUIPMENT_RATE_MC` — 7 rows
- `dbo.EC_METER_HISTORY`
- `dbo.EC_METER_HISTORY_MC` — 401 rows
- `dbo.EC_METER_READING`
- `dbo.EC_METER_READING_MC` — 0 rows
- `dbo.EC_RECUR_TRAN_EQUIP_XREF`
- `dbo.EC_RECUR_TRAN_EQUIP_XREF_MC`
- `dbo.EC_TEMP_EQUIP_CHARGE_REP`
- `dbo.EC_TEMP_EQUIP_CHARGE_REP_MC` — 0 rows
- `dbo.EC_TEMP_EQUIP_REVEN_HIST`
- `dbo.EC_TEMP_EQUIP_REVEN_HIST_MC` — 0 rows
- `dbo.EC_TEMP_EQUIP_UTIL`
- `dbo.EC_TEMP_EQUIP_UTIL_MC` — 0 rows
- `dbo.EC_TEMP_EQUIPMENT_CHANGE`
- `dbo.EC_TEMP_EQUIPMENT_CHANGE_MC` — 0 rows
- `dbo.EC_TEMP_EQUIPMENT_MASTER`

### GL / Finance  (320)

- `cdc.GL_BALANCE_MC_v1_CT` — 4,304 rows
- `cdc.GL_BUDGET_MC_v1_CT` — 0 rows
- `cdc.GL_DEPARTMENT_MC_v1_CT` — 0 rows
- `cdc.GL_DETAIL_MC_v1_CT` — 3,709 rows
- `cdc.GL_FISCAL_CALENDAR_DETAIL_v1_CT` — 0 rows
- `cdc.GL_MASTER_COST_CENTERS_MC_v1_CT` — 0 rows
- `cdc.GL_MASTER_MC_v1_CT` — 1 rows
- `cdc.PA_GLOBAL_BUSINESS_UNIT_MAP_v1_CT` — 0 rows
- `cdc.PA_GLOBAL_ENTITY_MAP_v1_CT` — 0 rows
- `cdc.PA_GLOBAL_TID_MAP_v1_CT` — 0 rows
- `cdc.PA_GLOBAL_USER_MAP_v1_CT` — 0 rows
- `cdc.VN_GL_DISTRIBUTION_DETAIL_MC_v1_CT` — 249 rows
- `cdc.VN_GL_DISTRIBUTION_HEADER_MC_v1_CT` — 165 rows
- `dbo.BI_BANK_ACCOUNT_MC_ID` — 24 rows
- `dbo.BR_BANK_ACCOUNT`
- `dbo.BR_BANK_ACCOUNT_MC` — 24 rows
- `dbo.BR_BANK_ACCOUNT_XREF`
- `dbo.BR_BANK_ACCOUNT_XREF_MC`
- `dbo.BR_CARD_ACCOUNT_DETAIL`
- `dbo.BR_CARD_ACCOUNT_DETAIL_MC` — 10 rows
- `dbo.BR_INTERCOMPANY_GL`
- `dbo.BR_INTERCOMPANY_GL_MC` — 0 rows
- `dbo.BR_MICR_BANK_ACCOUNT`
- `dbo.BR_MICR_BANK_ACCOUNT_MC` — 0 rows
- `dbo.BR_TEMP_BANK_ACCOUNT`
- `dbo.BR_TEMP_BANK_ACCOUNT_MC` — 0 rows
- `dbo.CP_TEMP_WC_REPORT_GL_SUM`
- `dbo.CP_TEMP_WC_REPORT_GL_SUM_MC` — 0 rows
- `dbo.CR_CASH_RECEIPT_GL_DETAIL`
- `dbo.CR_CASH_RECEIPT_GL_DETAIL_MC` — 12 rows
- `dbo.CR_CASH_RECEIPT_GL_HIST`
- `dbo.CR_CASH_RECEIPT_GL_HIST_MC` — 5,333 rows
- `dbo.CR_GL_HISTORY`
- `dbo.CR_GL_HISTORY_MC` — 25,280 rows
- `dbo.CR_TEMP_CASH_GL_HIST`
- `dbo.CR_TEMP_CASH_GL_HIST_MC` — 0 rows
- `dbo.CR_TEMP_CASH_REC_GL_UPD`
- `dbo.CR_TEMP_CASH_REC_GL_UPD_EQUIP_COSTS`
- `dbo.CR_TEMP_CASH_REC_GL_UPD_EQUIP_COSTS_MC` — 0 rows
- `dbo.CR_TEMP_CASH_REC_GL_UPD_MC` — 0 rows
- `dbo.CR_TEMP_GL`
- `dbo.CR_TEMP_GL_DIST_REP`
- `dbo.CR_TEMP_GL_DIST_REP_MC` — 0 rows
- `dbo.CR_TEMP_GL_HISTORY`
- `dbo.CR_TEMP_GL_HISTORY_MC` — 0 rows
- `dbo.CR_TEMP_GL_MC` — 0 rows
- `dbo.CR_TEMP_SALES_JOURNAL`
- `dbo.CR_TEMP_SALES_JOURNAL_MC` — 0 rows
- `dbo.EC_COST_CATEGORY_GL_RESTRICTION`
- `dbo.EC_COST_CATEGORY_GL_RESTRICTION_MC` — 0 rows
- `dbo.EC_DEPR_LICENSE_GL_WORK`
- `dbo.EC_DEPR_LICENSE_GL_WORK_MC` — 0 rows
- `dbo.EC_EQUIP_TYPE_BUDGET_COSTS`
- `dbo.EC_EQUIP_TYPE_BUDGET_DETAIL`
- `dbo.EC_EQUIP_TYPE_BUDGET_DETAIL_MC` — 0 rows
- `dbo.EC_EQUIP_TYPE_BUDGET_HEADER`
- `dbo.EC_EQUIP_TYPE_BUDGET_HEADER_MC` — 0 rows
- `dbo.EC_GL_WORK_HISTORY`
- `dbo.EC_GL_WORK_HISTORY_MC` — 698 rows
- `dbo.EC_INTERCOMP_GL_ACCOUNT`

### Service / Work Orders  (663)

- `cdc.PR_BASE_WORK_COMP_MC_v1_CT` — 0 rows
- `cdc.PR_WORK_CLASS_MC_v1_CT` — 0 rows
- `cdc.WO_ADDRESS_MC_v1_CT` — 0 rows
- `cdc.WO_DISPATCH_STATUS_MC_v1_CT` — 0 rows
- `cdc.WO_HEADER_MC_v1_CT` — 0 rows
- `cdc.WO_PRIORITY_MC_v1_CT` — 0 rows
- `cdc.WO_SITE_CONTACTS_MC_v1_CT` — 0 rows
- `dbo.BI_WORK_CLASS_MC_ID` — 34 rows
- `dbo.CP_TEMP_WORK_COMP_REP_2`
- `dbo.CP_TEMP_WORK_COMP_REP_2_MC` — 0 rows
- `dbo.CP_TEMP_WORKER_COMP_REP`
- `dbo.CP_TEMP_WORKER_COMP_REP_MC` — 0 rows
- `dbo.CR_CHANGE_REQUEST_WORKFLOW_MC` — 175 rows
- `dbo.CR_CUSTOMER_WORKFLOW_MC` — 0 rows
- `dbo.CR_DRAW_REQ_WORKFLOW_MC` — 0 rows
- `dbo.CR_TEMP_CO_AUDIT_RPTWO`
- `dbo.CR_TEMP_CO_AUDIT_RPTWO_MC` — 0 rows
- `dbo.CR_TEMP_WO_DETAIL`
- `dbo.CR_TEMP_WO_DETAIL_MC` — 0 rows
- `dbo.CR_TEMP_WO_HEADER`
- `dbo.CR_TEMP_WO_HEADER_MC` — 0 rows
- `dbo.EC_ACTUAL_COST_PM_WO_XREF`
- `dbo.EC_ACTUAL_COST_PM_WO_XREF_MC`
- `dbo.EC_DEPR_LICENSE_GL_WORK`
- `dbo.EC_DEPR_LICENSE_GL_WORK_MC` — 0 rows
- `dbo.EC_FIELD_SERVICE_SETUP_MC` — 0 rows
- `dbo.EC_GL_WORK_HISTORY`
- `dbo.EC_GL_WORK_HISTORY_MC` — 698 rows
- `dbo.EC_TEMP_WORKBOOK_LINK_MC` — 0 rows
- `dbo.EC_TRAN_GL_WORK`
- `dbo.EC_TRAN_GL_WORK_MC` — 0 rows
- `dbo.FT_EXCLUDED_WO_DISPATCH_STATUS`
- `dbo.FT_EXCLUDED_WO_DISPATCH_STATUS_MC` — 4 rows
- `dbo.FT_WO_MATERIAL`
- `dbo.FT_WO_OTHER_CHARGES`
- `dbo.FT_WO_PO_DETAIL`
- `dbo.GL_FORMULA_WORK` — 10 rows
- `dbo.GL_JE_WORKFLOW_MC` — 0 rows
- `dbo.GL_TEMP_WORKFILE2`
- `dbo.GL_TEMP_WORKFILE2_MC` — 0 rows
- `dbo.HR_APP_WORK_TAX_SETUP`
- `dbo.HR_APP_WORK_TAX_SETUP_MC` — 1 rows
- `dbo.JC_GL_WORK`
- `dbo.JC_GL_WORK_MC` — 30 rows
- `dbo.JC_JOB_WORKFLOW_MC` — 36 rows
- `dbo.JC_WO_V_MC`
- `dbo.PA_DATA_DISPATCH_DESC_DEFAULTS` — 1 rows
- `dbo.PA_DATA_WORKFLOW_FIELD_VALUES` — 81 rows
- `dbo.PA_DATA_WORKFLOW_FIELDS` — 126 rows
- `dbo.PA_DATA_WORKFLOW_KEYS` — 15 rows
- `dbo.PA_DATA_WORKFLOW_LINKS` — 46 rows
- `dbo.PA_DATA_WORKFLOW_LINKS_V`
- `dbo.PA_DATA_WORKFLOW_ROLE_TYPES` — 8 rows
- `dbo.PA_DATA_WORKFLOWS` — 9 rows
- `dbo.PA_FORGOT_PASSWORD_ENABLED`
- `dbo.PA_PASSWORD_REQUEST` — 0 rows
- `dbo.PA_PASSWORD_REQUEST_VALID`
- `dbo.PA_SERVICE_TECH_AUTHORIZATIONS`
- `dbo.PA_TEMP_WORKFLOW_MANAGEMENT_MC` — 0 rows
- `dbo.PA_TEMP_WORKFLOW_MANAGEMENT_V_MC`

## Columns — top 20 largest tables


### `dbo.AuditLogDetail` — 2,465,970 rows
- AuditLogID  `int NOT NULL`
- RowKey  `varchar(512) NOT NULL`
- ColumnID  `int NOT NULL`
- Status  `tinyint NOT NULL`
- OldValue  `varchar(3769)`
- NewValue  `varchar(3769)`

### `dbo.AuditLog` — 593,975 rows
- AuditLogID  `int NOT NULL`
- TableID  `int NOT NULL`
- RowsAffected  `int NOT NULL`
- Event  `char(1) NOT NULL`
- PostedDateTime  `datetime NOT NULL`
- UserName  `nvarchar(128) NOT NULL`
- HostName  `nvarchar(128) NOT NULL`
- ApplicationName  `nvarchar(128) NOT NULL`

### `dbo.PA_EVENT_LOG` — 252,598 rows
- Event_Key  `varchar(26) NOT NULL`
- Operator_Id  `varchar(3) NOT NULL`
- Company_Code  `varchar(3) NOT NULL`
- Logon_Id  `varchar(25) NOT NULL`
- Event_Description  `varchar(60) NOT NULL`
- Event_Date  `datetime NOT NULL`
- Event_Time  `varchar(6) NOT NULL`
- Event_Function  `varchar(32) NOT NULL`
- Event_Module  `varchar(6) NOT NULL`
- Database_Session  `varchar(12) NOT NULL`

### `dbo.MSchange_tracking_history` — 190,410 rows
- internal_table_name  `nvarchar(128) NOT NULL`
- table_name  `nvarchar(128) NOT NULL`
- start_time  `datetime NOT NULL`
- end_time  `datetime NOT NULL`
- rows_cleaned_up  `bigint NOT NULL`
- cleanup_version  `bigint NOT NULL`
- comments  `nvarchar NOT NULL`

### `dbo.PA_COLUMN_NAMES` — 169,407 rows
- TABLE_NAME  `varchar(80) NOT NULL`
- COLUMN_NUMBER  `varchar(3) NOT NULL`
- F_NAME  `varchar(40) NOT NULL`
- COLUMN_NAME  `varchar(40) NOT NULL`
- COLUMN_TYPE  `varchar(4) NOT NULL`
- COLUMN_DESC  `varchar(80) NOT NULL`

### `dbo.JC_TRANSACTION_HISTORY_MC` — 153,558 rows
- Company_Code  `varchar(3) NOT NULL`
- Job_Number  `varchar(10) NOT NULL`
- Phase_Code  `varchar(20) NOT NULL`
- Cost_Type  `varchar(3) NOT NULL`
- Tran_Type_Code  `varchar(2) NOT NULL`
- Tran_Date_Text  `varchar(8) NOT NULL`
- Reference_1  `varchar(15) NOT NULL`
- Reference_2  `varchar(20) NOT NULL`
- Detail_Sequence  `varchar(10) NOT NULL`
- Description  `varchar(30) NOT NULL`
- Employee_Code  `varchar(11) NOT NULL`
- Vendor_Code  `varchar(10) NOT NULL`
- Item_Code  `varchar(15) NOT NULL`
- Adjust_Reference  `varchar(15) NOT NULL`
- Invoice_Number  `varchar(20) NOT NULL`
- Invoice_Date  `datetime`
- Po_Number  `varchar(15) NOT NULL`
- Check_Number  `varchar(6) NOT NULL`
- Quantity  `decimal NOT NULL`
- Pr_Burden  `decimal NOT NULL`
- PR_Hours1  `decimal NOT NULL`
- PR_Hours2  `decimal NOT NULL`
- PR_Hours3  `decimal NOT NULL`
- PR_Hours4  `decimal NOT NULL`
- PR_Hours5  `decimal NOT NULL`
- PR_Hours6  `decimal NOT NULL`
- Total_Hours  `decimal NOT NULL`
- Tran_Amount  `decimal NOT NULL`
- PR_Pay_Amount1  `decimal NOT NULL`
- PR_Pay_Amount2  `decimal NOT NULL`
- PR_Pay_Amount3  `decimal NOT NULL`
- PR_Pay_Amount4  `decimal NOT NULL`
- PR_Pay_Amount5  `decimal NOT NULL`
- PR_Pay_Amount6  `decimal NOT NULL`
- PR_Pay_Amount7  `decimal NOT NULL`
- Pr_Company_Code  `varchar(3) NOT NULL`
- Employee_Name  `varchar(30) NOT NULL`
- AP_Company_Code  `varchar(3) NOT NULL`
- Vendor_Name  `varchar(30) NOT NULL`
- Equip_Company_Code  `varchar(3) NOT NULL`
- Batch_Code  `varchar(10) NOT NULL`
- Batch_Sequence  `decimal NOT NULL`
- Unit_of_Measure  `varchar(3) NOT NULL`
- Draw_Appl_Number  `varchar(3) NOT NULL`
- Customer_Code  `varchar(10) NOT NULL`
- Inventory_Company_Code  `varchar(3) NOT NULL`
- Item_Description  `varchar(35) NOT NULL`
- Crew_Number  `varchar(10) NOT NULL`
- Cost_Center  `varchar(10) NOT NULL`
- Tran_Date_Text_Year  `varchar(5) NOT NULL`
- Tran_Date_Text_Period  `varchar(2) NOT NULL`

### `dbo.PR_GL_HISTORY_MC` — 136,755 rows
- Company_Code  `varchar(3) NOT NULL`
- Alt_Company_Code  `varchar(3) NOT NULL`
- GL_Year  `varchar(2) NOT NULL`
- GL_Period  `varchar(2) NOT NULL`
- GL_Account  `varchar(12) NOT NULL`
- Cost_Center  `varchar(10) NOT NULL`
- Check_Number  `varchar(6) NOT NULL`
- Recon_Status_Flag  `varchar(1) NOT NULL`
- GL_Debit_Amount  `decimal NOT NULL`
- GL_Credit_Amount  `decimal NOT NULL`
- System_Key  `varchar(2) NOT NULL`
- GL_Key  `varchar(5) NOT NULL`
- Check_Date_List1  `datetime`
- Check_Date_List2  `datetime`
- Check_Date_List3  `datetime`
- Employee_Code  `varchar(11) NOT NULL`
- Operator_ID  `varchar(3) NOT NULL`

### `dbo.GL_DETAIL_MC` — 104,047 rows
- Company_Code  `varchar(3) NOT NULL`
- Year  `varchar(4) NOT NULL`
- Gl_Period  `varchar(2) NOT NULL`
- GL_Account  `varchar(12) NOT NULL`
- Tran_Ref_Days  `varchar(2) NOT NULL`
- Tran_Number  `varchar(10) NOT NULL`
- Reference_1  `varchar(1) NOT NULL`
- Reference_2  `varchar(15) NOT NULL`
- Reference_3  `varchar(20) NOT NULL`
- Reference_4  `varchar(25) NOT NULL`
- Tran_Date  `datetime`
- Amount  `decimal NOT NULL`
- Job_Number  `varchar(10) NOT NULL`
- Phase_Code  `varchar(20) NOT NULL`
- Cost_Type  `varchar(3) NOT NULL`
- Equipment_Code  `varchar(10) NOT NULL`
- Equipment_Cost_Category  `varchar(4) NOT NULL`
- Operator_ID  `varchar(3) NOT NULL`
- Transaction_ID  `varchar(10) NOT NULL`
- Inv_Comp_Code  `varchar(3) NOT NULL`
- Cost_Center  `varchar(10) NOT NULL`
- Matching_Cost_Center  `varchar(10) NOT NULL`
- WO_Number  `varchar(10) NOT NULL`
- WO_Equipment  `varchar(8) NOT NULL`
- WO_Component  `varchar(2) NOT NULL`
- WO_Contract  `varchar(10) NOT NULL`
- Journal_Remarks  `varchar(250) NOT NULL`
- Control_Code  `int NOT NULL`
- Source_Description  `varchar(30) NOT NULL`
- Job_Company  `char(3) NOT NULL`
- Equipment_Company  `char(3) NOT NULL`
- Vendor_Code  `char(10) NOT NULL`
- Vendor_Invoice_Number  `varchar(20) NOT NULL`
- Vendor_Invoice_Type  `char(1) NOT NULL`
- Cash_Management_Company  `char(3) NOT NULL`
- Cash_Management_Account  `varchar(15) NOT NULL`
- Check_Number  `varchar(6) NOT NULL`
- Cash_Management_Wire_Number  `varchar(5) NOT NULL`
- Cash_Management_Wire_Type  `varchar(1) NOT NULL`
- Customer_Code  `char(10) NOT NULL`
- Customer_Invoice_Number  `varchar(10) NOT NULL`
- Customer_Invoice_Type  `char(1) NOT NULL`
- Cash_Receipt_Transaction_Code  `varchar(10) NOT NULL`
- Cash_Receipt_Check_Number  `varchar(10) NOT NULL`
- GL_Journal_Entry_Company  `char(3) NOT NULL`
- GL_Journal_Entry_Number  `varchar(4) NOT NULL`
- Inventory_Company  `char(3) NOT NULL`
- Inventory_Transaction_Reference  `varchar(7) NOT NULL`
- DI_Company  `char(3) NOT NULL`
- DI_Cabinet  `varchar(15) NOT NULL`
- DI_Drawer  `varchar(20) NOT NULL`
- DI_Folder  `varchar(20) NOT NULL`
- DI_Reference  `varchar(60) NOT NULL`
- Source_Transaction_Type  `varchar(2) NOT NULL`

### `dbo.PR_TIME_CARD_HISTORY_MC` — 81,623 rows
- Company_Code  `varchar(3) NOT NULL`
- Employee_Code  `varchar(11) NOT NULL`
- Check_Sequence_Number  `varchar(1) NOT NULL`
- System_Key  `varchar(24) NOT NULL`
- Check_Type  `varchar(1) NOT NULL`
- Check_Number  `varchar(6) NOT NULL`
- Pay_Type  `varchar(10) NOT NULL`
- Day_Of_Week  `varchar(1) NOT NULL`
- Union_Code  `varchar(10) NOT NULL`
- Certified_Flag  `varchar(1) NOT NULL`
- Hours  `decimal NOT NULL`
- Pay_Rate_Code  `varchar(1) NOT NULL`
- Pay_Rate  `decimal NOT NULL`
- Pay_Extension  `decimal NOT NULL`
- Department_Code  `varchar(6) NOT NULL`
- Job_Number  `varchar(10) NOT NULL`
- Phase_Code  `varchar(20) NOT NULL`
- Cost_Type  `varchar(3) NOT NULL`
- Burden_Amount  `decimal NOT NULL`
- Worker_Comp_Code  `varchar(6) NOT NULL`
- PR_Update_Flag  `varchar(2) NOT NULL`
- Equipment_Code  `varchar(10) NOT NULL`
- Cost_Category  `varchar(4) NOT NULL`
- Equipment_Hours  `decimal NOT NULL`
- Equipment_Rate  `decimal NOT NULL`
- Check_Date  `datetime`
- Wage_Code  `varchar(10) NOT NULL`
- Billing_Rate  `decimal NOT NULL`
- Equipment_Bill_Rate  `decimal NOT NULL`
- Labor_Bill_Code  `varchar(3) NOT NULL`
- Equipment_Bill_Code  `varchar(3) NOT NULL`
- Period_End_Date  `datetime`
- Company_Code_2  `varchar(3) NOT NULL`
- Work_Date  `datetime`
- Work_State  `varchar(10) NOT NULL`
- Work_County  `varchar(10) NOT NULL`
- Work_Locality  `varchar(10) NOT NULL`
- Message  `varchar(30) NOT NULL`
- Union_Fringe  `decimal NOT NULL`
- Worker_Comp_Burden  `decimal NOT NULL`
- Worker_Comp_Deduct  `decimal NOT NULL`
- PM_WO_Number  `varchar(10) NOT NULL`
- Equipment_Rate_Flag  `varchar(1) NOT NULL`
- Certified_Job_Number  `varchar(10) NOT NULL`
- Calc_Flag  `varchar(1) NOT NULL`
- Incentive_Pay_Flag  `varchar(1) NOT NULL`
- Union_Fringe_Detail1  `decimal NOT NULL`
- Union_Fringe_Detail2  `decimal NOT NULL`
- Union_Fringe_Detail3  `decimal NOT NULL`
- Union_Fringe_Detail4  `decimal NOT NULL`
- Union_Fringe_Detail5  `decimal NOT NULL`
- Union_Fringe_Detail6  `decimal NOT NULL`
- Union_Fringe_Detail7  `decimal NOT NULL`
- Union_Fringe_Detail8  `decimal NOT NULL`
- Prevailing_Wage_Rate  `decimal NOT NULL`
- Repl_Check_Flag  `varchar(1) NOT NULL`
- Crew_Number  `varchar(10) NOT NULL`
- Cost_Center  `varchar(10) NOT NULL`
- Cash_Cost_Center  `varchar(10) NOT NULL`
- Bank_Account  `varchar(15) NOT NULL`

### `dbo.DI_JC_HISTORY_XREF_MC` — 76,929 rows
- Company_Code  `varchar(3) NOT NULL`
- Job_Number  `varchar(10) NOT NULL`
- Phase_Code  `varchar(20) NOT NULL`
- Cost_Type  `varchar(3) NOT NULL`
- Tran_Type_Code  `varchar(2) NOT NULL`
- Tran_Date_Text  `varchar(8) NOT NULL`
- Reference_1  `varchar(15) NOT NULL`
- Reference_2  `varchar(20) NOT NULL`
- Detail_Sequence  `varchar(10) NOT NULL`
- DI_Company  `varchar(3) NOT NULL`
- Cabinet  `varchar(15) NOT NULL`
- Drawer  `varchar(20) NOT NULL`
- Folder  `varchar(20) NOT NULL`
- Reference  `varchar(60) NOT NULL`

### `dbo.VN_GL_HISTORY_MC` — 76,263 rows
- Company_Code  `varchar(3) NOT NULL`
- Vendor_Code  `varchar(10) NOT NULL`
- Invoice_Number  `varchar(20) NOT NULL`
- Invoice_Type  `varchar(1) NOT NULL`
- Key_Field  `varchar(1) NOT NULL`
- Sequence  `varchar(3) NOT NULL`
- Company_Code2  `varchar(3) NOT NULL`
- GL_Account  `varchar(12) NOT NULL`
- Cost_Center  `varchar(10) NOT NULL`
- Debit_Amount  `decimal NOT NULL`
- Credit_Amount  `decimal NOT NULL`
- GL_Year  `varchar(2) NOT NULL`
- GL_Period  `varchar(2) NOT NULL`

### `dbo.Z_SpectrumLicenseUsageInfo` — 75,707 rows
- Date_Time  `datetime NOT NULL`
- User_ID  `char(3) NOT NULL`
- Active_Sessions  `int`

### `dbo.VN_GL_DISTRIBUTION_DETAIL_MC` — 58,614 rows
- Company_Code  `varchar(3) NOT NULL`
- Vendor_Code  `varchar(10) NOT NULL`
- Invoice_Number  `varchar(20) NOT NULL`
- Invoice_Type_Code  `varchar(1) NOT NULL`
- Sequence  `varchar(3) NOT NULL`
- GL_Distribution_Account  `varchar(12) NOT NULL`
- Debit_Amount  `decimal NOT NULL`
- Credit_Amount  `decimal NOT NULL`
- Job_Number  `varchar(10) NOT NULL`
- Phase_Code  `varchar(20) NOT NULL`
- Cost_Type  `varchar(3) NOT NULL`
- Remarks  `varchar(30) NOT NULL`
- Equipment_Code  `varchar(10) NOT NULL`
- Equipment_Category  `varchar(4) NOT NULL`
- Company_Code_2  `varchar(3) NOT NULL`
- This_Company_GL  `varchar(12) NOT NULL`
- Other_Company_GL  `varchar(12) NOT NULL`
- Unit_Of_Measure  `varchar(3) NOT NULL`
- Quantity  `decimal NOT NULL`
- Use_Tax_Code  `varchar(15) NOT NULL`
- Tax_Extension  `decimal NOT NULL`
- Tax_GL_Account  `varchar(12) NOT NULL`
- PM_Work_Order  `varchar(10) NOT NULL`
- Tax_Code  `varchar(15) NOT NULL`
- Taxable_Flag  `varchar(1) NOT NULL`
- Tax_Amount  `decimal NOT NULL`
- Tax_Percent  `decimal NOT NULL`
- Bid_Item_Number  `varchar(10) NOT NULL`
- Subcontractor_Worked_Hours1  `decimal NOT NULL`
- Subcontractor_Worked_Hours2  `decimal NOT NULL`
- Subcontractor_Worked_Hours3  `decimal NOT NULL`
- Subcontractor_Worked_Ext1  `decimal NOT NULL`
- Subcontractor_Worked_Ext2  `decimal NOT NULL`
- Subcontractor_Worked_Ext3  `decimal NOT NULL`
- Subcontractor_Message  `varchar(30) NOT NULL`
- Labor_Bill_Rate_Code  `varchar(10) NOT NULL`
- Cost_Center  `varchar(10) NOT NULL`
- WO_Number  `varchar(10) NOT NULL`
- Item_Code  `varchar(15) NOT NULL`
- Item_Desc  `varchar(35) NOT NULL`
- WO_Equipment  `varchar(8) NOT NULL`
- WO_Component  `varchar(2) NOT NULL`
- SC_Contract  `varchar(10) NOT NULL`
- Control_Code  `varchar(36) NOT NULL`
- WO_Unit_Price  `decimal NOT NULL`
- Unit_Price  `decimal NOT NULL`
- Current_Bill_Quantity  `decimal NOT NULL`
- Current_Bill_Amount  `decimal NOT NULL`
- Quantity_Billed_To_Date  `decimal NOT NULL`
- Amount_Billed_To_Date  `decimal NOT NULL`
- Estimated_Quantity  `decimal NOT NULL`
- Estimated_Bid  `decimal NOT NULL`
- Retention_Flag  `varchar(1) NOT NULL`
- Currency_Code  `varchar(3) NOT NULL`
- Exchange_Rate  `decimal NOT NULL`
- PO_Line_Sequence  `varchar(14) NOT NULL`
- Accrued_Cost  `decimal NOT NULL`
- Accrued_Cost_Exchange_Rate  `decimal NOT NULL`

### `dbo.PA_DATA_TABLE_FUNCTION_XREF` — 55,430 rows
- Function_Name  `varchar(32) NOT NULL`
- Cycle_Name  `varchar(32) NOT NULL`
- File_Number  `varchar(2) NOT NULL`
- Logic_Number  `varchar(3) NOT NULL`
- Logic_Line  `varchar(3) NOT NULL`
- Table_Name  `varchar(80) NOT NULL`
- File_Type  `varchar(10) NOT NULL`
- Method  `varchar(80) NOT NULL`
- File_Definition  `varchar(8) NOT NULL`
- Function_Type  `varchar(2) NOT NULL`
- Function_Title  `varchar(40) NOT NULL`

### `dbo.PA_DATA_FUNCTION_LINKS` — 42,722 rows
- Calling_Object  `varchar(32) NOT NULL`
- Calling_Object_Class  `varchar(2) NOT NULL`
- Called_Object  `varchar(32) NOT NULL`
- Called_Object_Class  `varchar(2) NOT NULL`
- Link_Sequence  `varchar(3) NOT NULL`

### `dbo.JC_PROJ_COST_HISTORY_MC` — 42,567 rows
- Company_Code  `varchar(3) NOT NULL`
- Job  `varchar(10) NOT NULL`
- Phase  `varchar(20) NOT NULL`
- Cost_Type  `varchar(3) NOT NULL`
- Type  `varchar(1) NOT NULL`
- System_Key  `varchar(24) NOT NULL`
- Year  `varchar(2) NOT NULL`
- Period  `varchar(2) NOT NULL`
- Transaction_Date  `datetime`
- Transaction_Time  `varchar(8) NOT NULL`
- Operator  `varchar(3) NOT NULL`
- Amount  `decimal NOT NULL`
- Variance  `decimal NOT NULL`
- Projected_Quantity  `decimal NOT NULL`
- Projected_Hours  `decimal NOT NULL`
- Remarks  `varchar(30) NOT NULL`
- Note  `varchar(80) NOT NULL`
- Transaction_Date_Year  `varchar(5) NOT NULL`
- Transaction_Date_Period  `varchar(2) NOT NULL`

### `dbo.DI_MASTER_MC` — 35,422 rows
- Company_Code  `varchar(3) NOT NULL`
- Cabinet  `varchar(15) NOT NULL`
- Drawer  `varchar(20) NOT NULL`
- Folder  `varchar(20) NOT NULL`
- Reference  `varchar(60) NOT NULL`
- Transaction_Description  `varchar(40) NOT NULL`
- Keywords  `varchar(200) NOT NULL`
- Transaction_ID  `uniqueidentifier NOT NULL`

### `dbo.VN_ROUTING_HISTORY_MC` — 35,355 rows
- Company_Code  `varchar(3) NOT NULL`
- Vendor_Code  `varchar(10) NOT NULL`
- Invoice_Number  `varchar(20) NOT NULL`
- Invoice_Type  `varchar(1) NOT NULL`
- Sequence  `varchar(3) NOT NULL`
- Description  `varchar(15) NOT NULL`
- Routing_ID  `varchar(3) NOT NULL`
- Routing_Name  `varchar(25) NOT NULL`
- Routing_Date  `datetime`
- Routing_Time  `varchar(8) NOT NULL`
- Routing_Status  `varchar(1) NOT NULL`
- Routing_By_ID  `varchar(3) NOT NULL`
- Approval_Limit  `decimal NOT NULL`

### `dbo.PR_TC_DET_UNION_FRI_HIST_MC` — 34,102 rows
- Company_Code  `varchar(3) NOT NULL`
- Employee_Code  `varchar(11) NOT NULL`
- Check_Sequence_Number  `varchar(1) NOT NULL`
- System_Key  `varchar(24) NOT NULL`
- Fringe_Code  `varchar(20) NOT NULL`
- Union_Code  `varchar(10) NOT NULL`
- Base_Type  `varchar(1) NOT NULL`
- Formula_Code  `varchar(5) NOT NULL`
- Fringe_Rate  `decimal NOT NULL`
- Fringe_Payable_GL  `varchar(12) NOT NULL`
- User_Defined_Var2  `decimal NOT NULL`
- User_Defined_Var3  `decimal NOT NULL`
- Fringe_Amount  `decimal NOT NULL`

### `dbo.PR_EMPL_TAX_HIST_EXEMPT_ADJ_MC` — 31,147 rows
- Company_Code  `varchar(3) NOT NULL`
- Employee_Code  `varchar(11) NOT NULL`
- Check_Number  `varchar(6) NOT NULL`
- Check_Type  `varchar(1) NOT NULL`
- Tax_Type  `varchar(1) NOT NULL`
- Tax_Table_Code  `varchar(10) NOT NULL`
- Pay_Type_Type  `varchar(1) NOT NULL`
- Pay_Type  `varchar(10) NOT NULL`
- Tax_Impacted  `varchar(1) NOT NULL`
- Exempt_Or_Adjust_Amount  `decimal NOT NULL`