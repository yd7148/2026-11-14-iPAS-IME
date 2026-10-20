$files = Get-ChildItem "D:\80-Opnecode\Projects\2026-11-14-iPAS-IME\01-原始擷取\*.md"
foreach ($f in $files) {
    $content = Get-Content $f.FullName -Raw
    $chars = $content.Length
    $lines = ($content -split "`n").Count
    Write-Host "$($f.Name)    $chars chars    $lines lines"
}