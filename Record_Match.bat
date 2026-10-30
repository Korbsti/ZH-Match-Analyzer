@echo off
title Zero Hour Match Statistics Enhancer
cd /d "%~dp0"
chcp 65001 >nul

echo ========================================================
echo    ZERO HOUR MATCH STATISTICS ENHANCER ^& RECORDER
echo ========================================================
echo.

:: 1. Launch the Replay Analyzer Dashboard in default web browser
if exist "ZH_Replay_Analyzer.html" (
    echo [*] Opening Analyzer Dashboard in your web browser...
    start "" "ZH_Replay_Analyzer.html"
)

:: 2. Check system PATH for python
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [*] Starting Live Telemetry Companion [python]...
    python -u zh_recorder.py
    goto done
)

:: 3. Check for py launcher
where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [*] Starting Live Telemetry Companion [py]...
    py -u zh_recorder.py
    goto done
)

:: 4. Check common Python installation paths
for %%p in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
) do (
    if exist "%%p" (
        echo [*] Starting Live Telemetry Companion [%%p]...
        "%%p" -u zh_recorder.py
        goto done
    )
)

echo.
echo ========================================================
echo [!] Python is not installed or not found in system PATH.
echo ========================================================
echo.
echo The Live Recorder companion uses Python 3 to record live
echo matches. (Note: You can still use ZH_Replay_Analyzer.html
echo directly in your browser without Python!)
echo.
echo Would you like to automatically install Python now via winget?
set /p INSTALL_CHOICE="Install Python now? (Y/N): "
if /i "%INSTALL_CHOICE%"=="Y" (
    echo [*] Installing Python via Windows Package Manager...
    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    echo.
    echo [✓] Installation complete! Please re-run Record_Match.bat.
    pause
    exit /b 0
)

echo.
echo You can manually download Python from: https://www.python.org/downloads/
echo (Important: Be sure to check "Add python.exe to PATH" during install!)
echo.
pause
exit /b 1

:done
echo.
pause
