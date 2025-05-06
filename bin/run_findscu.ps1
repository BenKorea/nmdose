# 필요 모듈 로딩
Import-Module powershell-yaml

# === 설정 로딩 ===
$pacs = ConvertFrom-Yaml (Get-Content "config\pacs.yaml" -Raw)
$config = ConvertFrom-Yaml (Get-Content "config\config.yaml" -Raw)

