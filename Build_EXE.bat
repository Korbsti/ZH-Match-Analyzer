@echo off
title Build ZH Match Analyzer EXE
cd /d "%~dp0"
chcp 65001 >nul

echo ========================================================
echo    BUILD  ZH_Match_Analyzer.exe
echo ========================================================
echo.

set PY=
where python >nul 2>nul && set PY=python
if "%PY%"=="" where py >nul 2>nul && set PY=py -3
if "%PY%"=="" (
    echo [!] Python 3 was not found. Install it from https://www.python.org/downloads/
    echo     ^(tick "Add python.exe to PATH"^) and run this file again.
    pause
    exit /b 1
)

echo [*] Installing PyInstaller...
%PY% -m pip install --upgrade pip pyinstaller
if errorlevel 1 goto fail

echo [*] Building the executable...
%PY% -m PyInstaller --noconfirm --clean --onefile --name ZH_Match_Analyzer ^
    --icon zh_icon.ico ^
    --add-data "ZH_Replay_Analyzer.html;." ^
    --add-data "zh_recorder.py;." ^
    zh_launcher.py
if errorlevel 1 goto fail

copy /y "dist\ZH_Match_Analyzer.exe" "ZH_Match_Analyzer.exe" >nul

echo.
echo [OK] Built ZH_Match_Analyzer.exe
echo      First launch creates the Desktop shortcut automatically.
echo.
start "" "ZH_Match_Analyzer.exe"
pause
exit /b 0

:fail
echo.
echo [!] Build failed - see the messages above.
pause
exit /b 1
