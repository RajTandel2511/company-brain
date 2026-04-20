$password = ConvertTo-SecureString 'North#121' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential('rag_indexer', $password)

# Massive candidate list — common Synology + construction industry names
$candidates = @(
    # Already known
    'home','homes','projects','accounting',
    # Common Synology defaults
    'public','shared','photo','video','music','web','download','downloads',
    'surveillance','surveillancestation','NetBackup','Drive','drive','usbshare',
    # Company org
    'common','everyone','staff','team','admin','administration','exec','management',
    # Departments
    'ar','ap','hr','payroll','finance','accounting2','billing','legal','marketing',
    'operations','engineering','estimating','procurement','purchasing','warehouse',
    'safety','compliance','training','it','tech','support','sales','bid','bidding',
    # Construction-specific
    'jobs','job','drawings','plans','specs','specifications','submittals','rfi',
    'rfis','rfq','changeorders','change_orders','contracts','permits','insurance',
    'bonding','prevailingwage','certified_payroll','unionpayroll','photos',
    'pictures','scans','reports','reports_archive','archive','old','legacy',
    'backup','backups','imports','import','exports','export','templates','forms',
    # Workflow
    'inbox','outbox','toreview','tofile','incoming','outgoing','dropbox',
    'received','sent','processed','pending','completed','approved',
    # Client-facing
    'client','clients','customer','customers','vendor','vendors','subs',
    'subcontractors','sub_folders',
    # Misc
    'data','files','docs','documents','cloud','cloudsync','dropzone',
    'spectrum','spectrum_backup','sql','database','db','logs','reports_sql',
    'allair','aam','all_air_mechanical','companydata','companyfiles',
    # Possible project tokens
    'bids_2024','bids_2025','bids_2026','2024','2025','2026',
    'completed_jobs','active_jobs','active','closed'
)

$results = @()
foreach ($s in $candidates) {
    try {
        # Use test-path directly via UNC — creds are in Credential Manager now
        if (Test-Path "\\10.231.0.3\$s" -ErrorAction Stop) {
            $results += $s
        }
    } catch { }
}
$results | Sort-Object -Unique | ForEach-Object { Write-Output $_ }
