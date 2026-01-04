@echo off
set "ROOT=%~dp0.."
set "PY=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not exist "%PY%" set "PY=python"
cd /d "%ROOT%"
del /Q "web\dashboard.html" 2>NUL
echo ========================================
echo  대시보드 재생성
echo ========================================
echo.
"%PY%" -B "src\regenerate_now.py"
echo.
pause
