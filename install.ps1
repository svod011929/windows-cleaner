# Установка Улучшенного Очистителя Windows - PowerShell скрипт

Write-Host "========================================" -ForegroundColor Green
Write-Host "  Установка Улучшенного Очистителя Windows" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Проверка прав администратора
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "Запрос прав администратора..." -ForegroundColor Yellow
    Start-Process PowerShell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

# Проверка версии Windows
$windowsVersion = [System.Environment]::OSVersion.Version
if ($windowsVersion.Major -ne 10 -and $windowsVersion.Major -ne 11) {
    Write-Host "ОШИБКА: Этот скрипт требует Windows 10 или 11" -ForegroundColor Red
    pause
    exit 1
}

# Функция проверки доступности команды
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Проверка и установка Python
if (-not (Test-Command "python")) {
    Write-Host "Python не найден. Установка..." -ForegroundColor Yellow
    $pythonUrl = "https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe"
    $installerPath = "$env:TEMP\python_installer.exe"
    
    try {
        Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath
        Start-Process -Wait -FilePath $installerPath -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1"
        Remove-Item $installerPath
        Write-Host "Python успешно установлен" -ForegroundColor Green
    }
    catch {
        Write-Host "Ошибка установки Python: $_" -ForegroundColor Red
        exit 1
    }
}

# Создание виртуального окружения
Write-Host "Создание виртуального окружения..." -ForegroundColor Yellow
python -m venv cleaner_venv

# Установка зависимостей
Write-Host "Установка зависимостей..." -ForegroundColor Yellow
& .\cleaner_venv\Scripts\pip.exe install --upgrade pip
& .\cleaner_venv\Scripts\pip.exe install tqdm winshell

# Создание скрипта запуска
$startupScript = @"
@echo off
chcp 65001 > nul
call cleaner_venv\Scripts\activate.bat
python enhanced_cleaner.py
pause
"@

$startupScript | Out-File -FilePath "run_cleaner.bat" -Encoding ASCII

# Создание ярлыка на рабочем столе
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$Home\Desktop\Очиститель Windows.lnk")
$Shortcut.TargetPath = "cmd.exe"
$Shortcut.Arguments = "/c run_cleaner.bat"
$Shortcut.WorkingDirectory = $PWD.Path
$Shortcut.IconLocation = "shell32.dll,31"
$Shortcut.Save()

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "   Установка успешно завершена!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nСозданные ярлыки:"
Write-Host "• run_cleaner.bat - Запуск очистителя"
Write-Host "• Ярлык на рабочем столе - Быстрый доступ" -ForegroundColor Cyan

pause
