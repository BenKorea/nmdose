[CmdletBinding()]
Param(
    [Parameter(Mandatory=$false)]
    [string]$ConfigPath = (
        Join-Path (
            Split-Path -Parent $PSScriptRoot
        ) 'config\config.json'
    ),

    [Parameter(Mandatory=$false)]
    [string]$LogDirectory = (
        Join-Path (
            Split-Path -Parent $PSScriptRoot
        ) 'logs'
    ),

    [Parameter(Mandatory=$false)]
    [string]$OutputDirectory = (
        Join-Path (
            Split-Path -Parent $PSScriptRoot
        ) 'output'
    )
)

#— 변수 초기화 & 경로 준비 —#
Set-StrictMode -Version Latest
foreach ($dir in @($LogDirectory, $OutputDirectory)) {
    if (-not (Test-Path $dir)) {
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
        Write-Verbose "Created directory: $dir"
    }
}

#— 로그 트랜스크립트 시작 —#
$TimeStamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$LogFile   = Join-Path $LogDirectory "sync_${TimeStamp}.log"
Start-Transcript -Path $LogFile -NoClobber

#— 설정파일 로딩 —#
$config     = Get-Content $ConfigPath   | ConvertFrom-Json
$AETLocal   = $config.NMPACS.CallingAET
$AETRemote  = $config.NMPACS.AET
$DicomHost  = $config.NMPACS.Host
$Port       = $config.NMPACS.Port
$Modality   = $config.Transfer.Modality

#— 날짜 범위 계산 —#
$StartDate  = $config.Transfer.StartDate            # ex: "20250101"
$EndDate    = (Get-Date).ToString('yyyyMMdd')       # 오늘 날짜
$DateRange  = "$StartDate-$EndDate"

Write-Host "Script running for StudyDate=$DateRange, Modality=$Modality" -ForegroundColor Cyan

#— 1) Query UIDs on NMPACS —#
Write-Host "Querying studies on NMPACS..." -ForegroundColor Yellow
$uids = @(
    & findscu -v -S -aet $AETLocal -aec $AETRemote `
    $DicomHost $Port `
    -k QueryRetrieveLevel=STUDY `
    -k StudyDate=$DateRange `
    -k ModalitiesInStudy=$Modality `
    -k StudyInstanceUID 2>&1 |
  Select-String 'StudyInstanceUID' |
  ForEach-Object { if ($_ -match 'UI \[([^\]]+)\]') { $matches[1] } }
)

$total = $uids.Count
Write-Host "Found $total studies from $StartDate to $EndDate." -ForegroundColor Green

# 스크립트 상단 어딘가에
[int]$n = 0
[bool]$ok = $false

if ($total -eq 0) {
    Write-Host "No studies to synchronize. Exiting." -ForegroundColor Magenta
    Stop-Transcript; return
}

#— 사용자로부터 처리할 개수 입력 —#
do {
    $input = Read-Host "몇 개를 추출하시겠습니까? (1–$total)"
    $ok = [int]::TryParse($input, [ref]$n)
    if (-not $ok -or $n -lt 1) {
        Write-Host "올바른 숫자를 입력하세요." -ForegroundColor Red
    }
} until ($ok -and $n -ge 1)

#— 입력값 클램프 —#
if ($n -gt $total) {
    Write-Host "입력값이 총 개수($total)를 넘었습니다. 전체 $total건을 처리합니다." -ForegroundColor Yellow
    $n = $total
}

$uids = $uids[0..($n - 1)]
Write-Host "▶ 추출 대상: 처음 $n 개의 StudyInstanceUID" -ForegroundColor Cyan

#— 2) Execute C-MOVE for each 선택된 UID —#
Write-Host "Starting C-MOVE operations..." -ForegroundColor Yellow
foreach ($uid in $uids) {
    Write-Host "Moving study UID: $uid" -ForegroundColor Yellow
    movescu -v -S -aet $AETLocal -aec $AETRemote -aem $AETLocal `
        $DicomHost $Port `
        -k QueryRetrieveLevel=STUDY `
        -k StudyInstanceUID=$uid
    Write-Host "Completed move for UID: $uid" -ForegroundColor Green
    Write-Host ""
}

Write-Host "All C-MOVE requests completed." -ForegroundColor Cyan
Stop-Transcript
