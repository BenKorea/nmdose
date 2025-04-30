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

#— Strict 모드 & 디렉터리 준비 —#
Set-StrictMode -Version Latest

foreach ($dir in @($LogDirectory, $OutputDirectory)) {
    if (-not (Test-Path $dir)) {
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
        Write-Verbose "Created directory: $dir"
    }
}

#— 로그 파일 생성 & 트랜스크립트 시작 —#
$TimeStamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$LogFile   = Join-Path $LogDirectory "sync_${TimeStamp}.log"

Start-Transcript -Path $LogFile -NoClobber

# (이전 Param, 디렉터리 준비, 트랜스크립트 등 생략)

# 설정 로드
$config      = Get-Content $ConfigPath | ConvertFrom-Json
$AETLocal    = $config.NMPACS.CallingAET
$AETRemote   = $config.NMPACS.AET
$DicomHost   = $config.NMPACS.Host
$Port        = $config.NMPACS.Port
$DateRange   = $config.Transfer.DateRange
$Modalities  = $config.Transfer.Modalities  # 이제 배열

Write-Host "Script started for date range $DateRange and modalities $($Modalities -join ',')" -ForegroundColor Cyan

# 1) Query UIDs on NMPACS for each Modality
Write-Host "Querying studies on NMPACS..." -ForegroundColor Yellow
$allUids = foreach ($mod in $Modalities) {
    Write-Host " • Modality = $mod" -ForegroundColor DarkYellow
    & findscu -v -S `
        -aet $AETLocal `
        -aec $AETRemote $DicomHost $Port `
        -k QueryRetrieveLevel=STUDY `
        -k StudyDate=$DateRange `
        -k ModalitiesInStudy=$mod `
        -k StudyInstanceUID 2>&1 |
    Select-String 'StudyInstanceUID' |
    ForEach-Object {
        if ($_ -match 'UI \[([^\]]+)\]') { $matches[1] }
    }
}

# 중복 제거
$uids = $allUids | Sort-Object -Unique

Write-Host "Total unique UIDs found: $($uids.Count)" -ForegroundColor Green

# 2) Execute C-MOVE for each UID
Write-Host "Starting C-MOVE operations..." -ForegroundColor Yellow
foreach ($uid in $uids) {
    Write-Host "Moving study UID: $uid" -ForegroundColor Yellow
    movescu -v -S `
        -aet $AETLocal `
        -aec $AETRemote `
        -aem $AETLocal $DicomHost $Port `
        -k QueryRetrieveLevel=STUDY `
        -k StudyInstanceUID=$uid 2>&1
    Write-Host "Completed move for UID: $uid" -ForegroundColor Green
    Write-Host ""
}

Write-Host "All C-MOVE requests completed." -ForegroundColor Cyan
Stop-Transcript
