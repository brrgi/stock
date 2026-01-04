@echo off
set "ROOT=%~dp0.."
set "PY=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not exist "%PY%" set "PY=python"
cd /d "%ROOT%"
"%PY%" -B "src\backtest_weekly.py"
pause
