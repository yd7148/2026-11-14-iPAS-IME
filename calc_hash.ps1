$files = Get-ChildItem "D:\80-Opnecode\Projects\2026-11-14-iPAS-IME\*.pdf"
foreach ($f in $files) {
    $hash = Get-FileHash -Algorithm SHA256 $f.FullName
    $sizeKB = [math]::Round($f.Length / 1KB, 2)
    Write-Host "$($f.Name)`t$sizeKB KB`t$($hash.Hash)"
}