@echo off
title ZH Match Analyzer
cd /d "%~dp0"
where python >nul 2>nul && (python zh_launcher.py %* & goto :eof)
where py >nul 2>nul && (py -3 zh_launcher.py %* & goto :eof)
echo Python 3 is required (or run Build_EXE.bat on a PC that has it).
pause
