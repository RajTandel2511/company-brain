# Store NAS credentials at the Windows Credential Manager so ANY process this
# user starts (including Python scripts, background services) can reach the share
# over UNC paths without prompting.
cmd /c "cmdkey /add:10.231.0.3 /user:rag_indexer /pass:North#121" | Out-Null
Write-Output "Stored credentials for 10.231.0.3 (user rag_indexer) in Credential Manager"

# Accessible shares — all 26 discovered from DSM Control Panel screenshot.
$shares = @(
    'Accounting','ActiveBackupforBusiness','AI_RAG_Data','All_Air_Users',
    'Common_Submittals','Current_Bids','Employee Resources','Estimation',
    'Foremen Portal','Forms','home','homes','Inventory','Miscallaneous',
    'NetBackup','netlogon','Office_Use_Only','Projects','RemotDrive',
    'Scripts','Service Tech Portal','Service_Dept','sysvol','Trial-1',
    'Vulacan Desktop-140','web'
)

# Also probe for any new shares that may have been granted since.
$candidates = @(
    'public','shared','documents','docs','data','jobs','company','files',
    'archive','scans','photos','drawings','plans','bids','submittals','rfi',
    'contracts','legal','operations','engineering','safety','hr','payroll'
)
$extra = @()
foreach ($s in $candidates) {
    if ($shares -contains $s) { continue }
    try { New-PSDrive -Name TMP -PSProvider FileSystem -Root "\\10.231.0.3\$s" -ErrorAction Stop | Out-Null
          Remove-PSDrive -Name TMP -ErrorAction SilentlyContinue; $extra += $s } catch {}
}
if ($extra.Count) { Write-Output ("Also accessible: " + ($extra -join ', ')); $shares += $extra }

# Build C:\nas root with SYMBOLIC links (not junctions). Symbolic links to UNC
# paths work across processes; junctions + mapped drives don't.
$root = 'C:\nas'
if (-not (Test-Path $root)) { New-Item -ItemType Directory -Path $root | Out-Null }

foreach ($s in $shares) {
    # Replace spaces with underscores in the local link name so paths stay clean
    $linkName = $s -replace ' ', '_'
    $link = Join-Path $root $linkName
    if (Test-Path $link) {
        cmd /c "rmdir /S /Q `"$link`"" 2>$null | Out-Null
        if (Test-Path $link) { cmd /c "del /F /Q `"$link`"" 2>$null | Out-Null }
    }
    # Verify the share is actually reachable before linking — skip silently if not
    if (-not (Test-Path "\\10.231.0.3\$s" -ErrorAction SilentlyContinue)) {
        Write-Output "SKIP (no access): $s"
        continue
    }
    cmd /c "mklink /D `"$link`" `"\\10.231.0.3\$s`"" | Out-Null
}

Write-Output ""
Write-Output "NAS_ROOT = C:\nas now contains:"
Get-ChildItem C:\nas -Force | Select-Object Name, Mode, Target | Format-Table -AutoSize
