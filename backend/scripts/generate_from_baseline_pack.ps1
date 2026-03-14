param(
  [Parameter(Mandatory = $true)]
  [string]$SourceXlsx,
  [string]$OutputDir = "data"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Convert-ColumnRefToIndex {
  param([string]$ColumnRef)
  $letters = ($ColumnRef -replace '\d', '').ToUpperInvariant()
  $index = 0
  foreach ($char in $letters.ToCharArray()) {
    $index = ($index * 26) + ([int][char]$char - [int][char]'A' + 1)
  }
  return $index - 1
}

function Get-CellValue {
  param($cell)
  if ($null -eq $cell) { return "" }
  if ($cell.t -eq "inlineStr") {
    if ($null -ne $cell.is -and $null -ne $cell.is.t) { return [string]$cell.is.t }
    return ""
  }
  if ($null -ne $cell.v) { return [string]$cell.v }
  return ""
}

function Get-SheetRows {
  param([string]$SheetPath)
  [xml]$xml = Get-Content $SheetPath
  $rows = @()
  foreach ($row in $xml.worksheet.sheetData.row) {
    $cells = @{}
    foreach ($cell in $row.c) {
      $index = Convert-ColumnRefToIndex -ColumnRef ([string]$cell.r)
      $cells[$index] = Get-CellValue -cell $cell
    }
    $max = -1
    foreach ($key in $cells.Keys) {
      if ($key -gt $max) { $max = $key }
    }
    $rowValues = @()
    for ($i = 0; $i -le $max; $i++) {
      if ($cells.ContainsKey($i)) { $rowValues += $cells[$i] } else { $rowValues += "" }
    }
    $rows += ,$rowValues
  }
  return $rows
}

function Convert-ExcelDateTime {
  param([string]$SerialText)
  if ([string]::IsNullOrWhiteSpace($SerialText)) { return "" }
  $serial = [double]$SerialText
  $base = [datetime]"1899-12-30T00:00:00"
  $dt = $base.AddDays($serial)
  return $dt.ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function Convert-DayNameToIndex {
  param([string]$DayName)
  $map = @{
    "monday"    = 0
    "tuesday"   = 1
    "wednesday" = 2
    "thursday"  = 3
    "friday"    = 4
    "saturday"  = 5
    "sunday"    = 6
  }
  $key = $DayName.Trim().ToLowerInvariant()
  if ($map.ContainsKey($key)) { return $map[$key] }
  return -1
}

function Get-Stats {
  param([double[]]$Values)
  if ($Values.Count -eq 0) { return @{ mean = 0.0; std = 1.0 } }
  $mean = ($Values | Measure-Object -Average).Average
  if ($Values.Count -le 1) { return @{ mean = [double]$mean; std = 1.0 } }
  $sumSquares = 0.0
  foreach ($value in $Values) {
    $sumSquares += [math]::Pow($value - $mean, 2)
  }
  $std = [math]::Sqrt($sumSquares / ($Values.Count - 1))
  if ($std -lt 0.000001) { $std = 1.0 }
  return @{ mean = [double]$mean; std = [double]$std }
}

$root = Split-Path -Parent $PSScriptRoot
$outPath = Join-Path $root $OutputDir
if (!(Test-Path $outPath)) { New-Item -ItemType Directory -Path $outPath | Out-Null }

$stamp = Get-Date -Format "yyyyMMddHHmmss"
$zipPath = Join-Path $root "__baseline_pack_$stamp.zip"
$extractPath = Join-Path $root "__baseline_pack_$stamp"
Copy-Item $SourceXlsx $zipPath
Expand-Archive -LiteralPath $zipPath -DestinationPath $extractPath

$sheet1Rows = Get-SheetRows -SheetPath (Join-Path $extractPath "xl\\worksheets\\sheet1.xml")
$headers = $sheet1Rows[0]
$windows = @()
for ($rowIndex = 1; $rowIndex -lt $sheet1Rows.Count; $rowIndex++) {
  $row = $sheet1Rows[$rowIndex]
  $obj = [ordered]@{}
  for ($col = 0; $col -lt $headers.Count; $col++) {
    $name = $headers[$col]
    $obj[$name] = if ($col -lt $row.Count) { $row[$col] } else { "" }
  }
  $obj["timestamp_start"] = Convert-ExcelDateTime -SerialText $obj["timestamp_start"]
  $obj["day_of_week"] = Convert-DayNameToIndex -DayName $obj["day_of_week"]
  $obj["hour_of_day"] = [int]$obj["hour_of_day"]
  $obj["is_workday"] = if ([double]$obj["is_workday"] -ge 1) { "true" } else { "false" }
  $windows += [pscustomobject]$obj
}

$windows |
  Select-Object user_id, timestamp_start, day_of_week, hour_of_day, is_workday, scenario_label, active_minutes, afk_minutes, afk_count, app_switch_count, distinct_app_count, top_app_category, email_minutes, chat_minutes, browser_minutes, docs_minutes, ide_minutes, meeting_minutes, admin_minutes, focus_streak_minutes, work_context_entropy, work_reentry_count |
  Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $outPath "synthetic_windows.csv")

$core = @(
  "app_switch_count",
  "distinct_app_count",
  "focus_streak_minutes",
  "afk_count",
  "afk_minutes",
  "work_context_entropy",
  "work_reentry_count"
)
$lowerIsWorse = @("focus_streak_minutes")

$baselineRows = @()
$globalGroups = $windows | Group-Object day_of_week, hour_of_day
foreach ($group in $globalGroups) {
  $sample = $group.Group[0]
  $row = [ordered]@{
    user_id = "global"
    day_of_week = [int]$sample.day_of_week
    hour_of_day = [int]$sample.hour_of_day
  }
  foreach ($feature in $core) {
    $vals = @()
    foreach ($item in $group.Group) { $vals += [double]$item.$feature }
    $stats = Get-Stats -Values $vals
    $row["${feature}_mean"] = [math]::Round($stats.mean, 6)
    $row["${feature}_std"] = [math]::Round($stats.std, 6)
  }
  $baselineRows += [pscustomobject]$row
}

$userGroups = $windows | Group-Object user_id, day_of_week, hour_of_day
foreach ($group in $userGroups) {
  $sample = $group.Group[0]
  $row = [ordered]@{
    user_id = [string]$sample.user_id
    day_of_week = [int]$sample.day_of_week
    hour_of_day = [int]$sample.hour_of_day
  }
  foreach ($feature in $core) {
    $vals = @()
    foreach ($item in $group.Group) { $vals += [double]$item.$feature }
    $stats = Get-Stats -Values $vals
    $row["${feature}_mean"] = [math]::Round($stats.mean, 6)
    $row["${feature}_std"] = [math]::Round($stats.std, 6)
  }
  $baselineRows += [pscustomobject]$row
}

$baselineRows |
  Sort-Object user_id, day_of_week, hour_of_day |
  Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $outPath "baseline_profile.csv")

$globalStats = @{}
foreach ($feature in $core) {
  $vals = @()
  foreach ($window in $windows) { $vals += [double]$window.$feature }
  $globalStats[$feature] = Get-Stats -Values $vals
}

$scenarioGroups = $windows | Group-Object scenario_label
$scenarioRows = @()
foreach ($group in $scenarioGroups) {
  $label = [string]$group.Name
  $row = [ordered]@{
    scenario_label = $label
    sample_windows = $group.Count
  }
  foreach ($feature in $core) {
    $vals = @()
    foreach ($item in $group.Group) { $vals += [double]$item.$feature }
    $mean = (Get-Stats -Values $vals).mean
    $stats = $globalStats[$feature]
    if ($lowerIsWorse -contains $feature) {
      $z = ($stats.mean - $mean) / $stats.std
    } else {
      $z = ($mean - $stats.mean) / $stats.std
    }
    $row[$feature] = [math]::Round($z, 6)
  }
  $scenarioRows += [pscustomobject]$row
}

$scenarioRows |
  Sort-Object scenario_label |
  Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $outPath "scenario_centroids.csv")

Write-Output "Generated:"
Write-Output (Join-Path $outPath "baseline_profile.csv")
Write-Output (Join-Path $outPath "scenario_centroids.csv")
Write-Output (Join-Path $outPath "synthetic_windows.csv")
