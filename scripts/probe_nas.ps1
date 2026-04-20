$password = ConvertTo-SecureString 'North#121' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential('rag_indexer', $password)

$candidates = @(
    'home','homes','public','shared','documents','docs','data',
    'projects','jobs','allair','company','files','archive',
    'rag','rag_index','indexer','spectrum','accounting',
    'ar','ap','hr','payroll','estimating','drawings','plans'
)

foreach ($share in $candidates) {
    $unc = "\\10.231.0.3\$share"
    try {
        New-PSDrive -Name T -PSProvider FileSystem -Root $unc -Credential $cred -ErrorAction Stop | Out-Null
        Write-Output "OK: $unc"
        Remove-PSDrive -Name T -ErrorAction SilentlyContinue
    } catch {
        # silent
    }
}
Write-Output "done"
