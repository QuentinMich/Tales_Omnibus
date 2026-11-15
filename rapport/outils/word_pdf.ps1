param([string]$docx, [string]$pdf)
$w = New-Object -ComObject Word.Application
$w.Visible = $false
$w.DisplayAlerts = 0
try {
    $d = $w.Documents.Open($docx, $false, $false)
    foreach ($toc in $d.TablesOfContents) { $toc.Update() }
    $d.Save()
    $d.ExportAsFixedFormat($pdf, 17)
    "Pages : " + $d.ComputeStatistics(2)
    $d.Close($false)
} finally { $w.Quit() }
