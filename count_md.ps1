$files = Get-ChildItem "D:\80-Opnecode\Projects\2026-11-14-iPAS-IME\01-原始擷取\*.md"
foreach ($f in $files) {
    $content = Get-Content $f.FullName -Raw
    $charCount = $content.Length
    $lineCount = ($content -split "`n").Count
    $wordCount = ($content -split "\s+").Count
    Write-Host "$($f.Name)`t$charCount chars`t$lineCount lines`t$wordCount words"
}