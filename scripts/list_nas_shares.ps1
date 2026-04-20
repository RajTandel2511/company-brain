$password = ConvertTo-SecureString 'North#121' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential('rag_indexer', $password)
try {
    $session = New-CimSession -ComputerName 10.231.0.3 -Credential $cred -ErrorAction Stop
    Get-SmbShare -CimSession $session | Select-Object -ExpandProperty Name
} catch {
    Write-Output ("ERR: " + $_.Exception.Message)
}
