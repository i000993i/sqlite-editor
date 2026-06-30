param(
    [switch]$Console
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectRoot

# Проверка зависимостей
Write-Host "Проверка зависимостей..." -ForegroundColor Cyan
try {
    python -m pip install -r requirements.txt 2>&1 | Out-Null
} catch {
    Write-Warning "Ошибка установки зависимостей, продолжаем..."
}

# Установка PyInstaller
Write-Host "Установка PyInstaller..." -ForegroundColor Cyan
python -m pip install pyinstaller 2>&1 | Out-Null

# Очистка старых сборок
if (Test-Path 'dist') { Remove-Item -Recurse -Force 'dist' }
if (Test-Path 'build') { Remove-Item -Recurse -Force 'build' }

# Выбор spec с консолью или без
$SpecFile = if ($Console) { 'SQLiteViewer_console.spec' } else { 'SQLiteViewer.spec' }

Write-Host "Сборка приложения..." -ForegroundColor Cyan
python -m PyInstaller $SpecFile --noconfirm

# Копируем иконки (на случай если spec не сработал)
$DistIcons = "dist\SQLiteViewer\icons"
if (!(Test-Path $DistIcons)) {
    Copy-Item -Recurse 'icons' 'dist\SQLiteViewer\icons'
}

Write-Host ""
Write-Host "Готово! Исполняемый файл:" -ForegroundColor Green
Write-Host "  dist\SQLiteViewer\SQLiteViewer.exe" -ForegroundColor Yellow
if (-not $Console) {
    Write-Host ""
    Write-Host "Для сборки с консолью (отладка):" -ForegroundColor Gray
    Write-Host "  .\build_app.ps1 -Console" -ForegroundColor Gray
}
