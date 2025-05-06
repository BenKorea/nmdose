<#
.SYNOPSIS
    NMDOSE 설정 파일들을 불러와 전역 변수로 로딩합니다.
.DESCRIPTION
    config.yaml, pacs.yaml 등의 설정 파일을 읽고,
    해당 값을 전역 변수로 설정합니다.
.EXPORTS
    Import-NMDoseConfig
#>

function Import-NMDoseConfig {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [string]$ConfigPath
    )

    # YAML 모듈 확인 및 로드
    if (-not (Get-Module -Name powershell-yaml -ListAvailable)) {
        Write-Error "powershell-yaml 모듈이 설치되어 있지 않습니다. Install-Module -Name powershell-yaml 로 설치하세요."
        return
    }
    Import-Module powershell-yaml -ErrorAction Stop

    try {
        $global:NMDOSE_Config = ConvertFrom-Yaml (Get-Content (Join-Path $ConfigPath 'config.yaml') -Raw)
        $global:NMDOSE_PACS   = ConvertFrom-Yaml (Get-Content (Join-Path $ConfigPath 'pacs.yaml') -Raw)

        # 유용한 전역 단축 변수 설정
        $global:debug_mode = ($global:NMDOSE_Config.debug_mode -eq 1)
        $global:run_mode   = if ($global:NMDOSE_PACS.mode -eq 1) { "clinical" } else { "simulation" }

        Write-Host "[설정 로드 완료] 모드: $run_mode, 디버그: $debug_mode"
    }
    catch {
        Write-Error "설정 파일 로딩 중 오류 발생: $($_.Exception.Message)"
    }
}

# 함수 내보내기
Export-ModuleMember -Function Import-NMDoseConfig
