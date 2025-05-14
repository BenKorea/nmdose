# ──────────────────────────────────────────────────────────────────────────────
# test.ps1
# ──────────────────────────────────────────────────────────────────────────────
# (1) 스크립트 위치 기준으로 config 폴더 경로 지정
$ConfigPath = Join-Path $PSScriptRoot '..\config\config.yaml'

# (2) 파일 전체를 -Raw 로 읽고, ConvertFrom-Yaml 로 객체로 변환
$config = Get-Content -Path $ConfigPath -Raw | ConvertFrom-Yaml

# (3) clinical_to_research 밑의 modalities 배열 추출
$Modalities = $config.clinical_to_research.modalities
if (-not $Modalities) {
    Write-Error "config.yaml 에 clinical_to_research.modalities 가 정의되어 있지 않습니다."
    exit 1
}

# (4) PACS 연결 정보도 pacs.yaml 에 분리되어 있다면 마찬가지로 읽기
#    예시: pacs.yaml 에 NMPACS: { CallingAET: ..., AET: ..., Host: ..., Port: ... }
$pacsConfigPath = Join-Path $PSScriptRoot '..\config\pacs.yaml'
$pacs    = Get-Content -Path $pacsConfigPath -Raw | ConvertFrom-Yaml

$AETLocal  = $pacs.NMPACS.CallingAET
$AETRemote = $pacs.NMPACS.AET
$Host      = $pacs.NMPACS.Host
$Port      = $pacs.NMPACS.Port

# (5) 로그 디렉터리 보장
$logDir = Join-Path $PSScriptRoot '..\logs'
if (-not (Test-Path $logDir)) { New-Item -Path $logDir -ItemType Directory | Out-Null }

# (6) PT, NM 루프
foreach ($MOD in $Modalities) {
    Write-Host "`n=== Querying modality: $MOD ===" -ForegroundColor Cyan

    findscu `
      -v -S `
      -aet $AETLocal -aec $AETRemote `
      $Host $Port `
      -k QueryRetrieveLevel=STUDY `
      -k ModalitiesInStudy=$MOD `
      -k StudyInstanceUID `
      -k StudyDate |
        Tee-Object -FilePath (Join-Path $logDir "findscu_${MOD}.log")
}

Write-Host "`n모든 모달리티에 대한 조회가 완료되었습니다."
# ──────────────────────────────────────────────────────────────────────────────

