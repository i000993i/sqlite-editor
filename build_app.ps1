param([switch]$Console)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$args = @()
if ($Console) { $args += '--console' }
python .\build.py @args