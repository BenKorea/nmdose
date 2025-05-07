[CmdletBinding()]
Param(
    [Parameter(Mandatory=$false)]
    [string]$ConfigPath = (
        Join-Path (Split-Path -Parent $PSScriptRoot) 'config\config.json'
    )
)

#— 설정 로드 (DateRange 만) —#
$config    = Get-Content $ConfigPath | ConvertFrom-Json
$DateRange = $config.Transfer.DateRange

# 데이터의 날짜가 맞지 않아 테스트를 위해 임시로 설정
$DateRange = "20240101-20240331"

#— 고정 변수 —#
$AETLocal  = "DICOOGLE-STORAGE"
$AETRemote = "ORTHANC"
$DicomHost = "127.0.0.1"
$Port      = 4242
$Modality  = "SR"    # Structured Report

Write-Host "Script started for date range $DateRange and modality $Modality" -ForegroundColor Cyan

# 1) Study 레벨에서 SR 포함된 Study 찾기
$studyUIDs = & findscu -v -S `
    -aet $AETLocal `
    -aec $AETRemote `
    $DicomHost $Port `
    -k QueryRetrieveLevel=STUDY `
    -k StudyDate=$DateRange `
    -k ModalitiesInStudy=SR `
    -k StudyInstanceUID 2>&1 |
  Select-String 'StudyInstanceUID' |
  ForEach-Object { if ($_ -match 'UI \[([^\]]+)\]') { $matches[1] } }

Write-Host "Found $($studyUIDs.Count) SR studies." -ForegroundColor Green

# 2) 각 Study 안의 SR Series 찾기
$allSeries = foreach ($stu in $studyUIDs) {
    & findscu -v -S `
        -aet $AETLocal `
        -aec $AETRemote `
        $DicomHost $Port `
        -k QueryRetrieveLevel=SERIES `
        -k StudyInstanceUID=$stu `
        -k Modality=SR `
        -k SeriesInstanceUID 2>&1 |
      Select-String 'SeriesInstanceUID' |
      ForEach-Object { if ($_ -match 'UI \[([^\]]+)\]') { $matches[1] } }
}

$seriesUIDs = $allSeries | Sort-Object -Unique
Write-Host "Total SR series found: $($seriesUIDs.Count)" -ForegroundColor Green

foreach ($series in $seriesUIDs) {
    movescu -v -S `
      -aet $AETLocal `
      -aec $AETRemote `
      -aem $AETLocal `
      $DicomHost $Port `
      -k QueryRetrieveLevel=SERIES `
      -k SeriesInstanceUID=$series
    Write-Host "Moved Series $series" -ForegroundColor Cyan
}