@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ========================================
echo   Установка Улучшенного Очистителя Windows
echo ========================================

:: Проверка версии Windows
ver | find "10." > nul
if %errorlevel% neq 0 (
    ver | find "11." > nul
    if %errorlevel% neq 0 (
        echo ОШИБКА: Этот скрипт требует Windows 10 или 11
        pause
        exit /b 1
    )
)

:: Проверка Python
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Установка Python...
    powershell -Command "Start-Process -Wait -FilePath 'https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe' -ArgumentList '/quiet', 'InstallAllUsers=1', 'PrependPath=1'"
) else (
    echo Python найден: Проверка версии...
    python -c "import sys; print('Python', sys.version)"
)

:: Создание виртуального окружения
echo Создание виртуального окружения...
python -m venv cleaner_venv
call cleaner_venv\Scripts\activate.bat

:: Установка зависимостей
echo Установка зависимостей...
pip install --upgrade pip
pip install tqdm winshell

:: Создание скрипта запуска
echo Создание скрипта запуска...
echo @echo off > run_cleaner.bat
echo chcp 65001 > nul >> run_cleaner.bat
echo call cleaner_venv\Scripts\activate.bat >> run_cleaner.bat
echo python enhanced_cleaner.py >> run_cleaner.bat
echo pause >> run_cleaner.bat

echo.
echo ========================================
echo    Установка успешно завершена!
echo ========================================
echo.
echo Запустите 'run_cleaner.bat' для старта очистителя
echo.

pause
