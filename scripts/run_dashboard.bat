@echo off
set "ROOT=%~dp0.."
set "PY=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not exist "%PY%" set "PY=python"
cd /d "%ROOT%"
del /Q "web\dashboard.html" 2>NUL
echo ========================================
echo  Dashboard.html 생성
echo ========================================
echo.
"%PY%" -B "src\create_current_dashboard.py"
echo.
echo ========================================
echo  완료!
echo ========================================
pause
