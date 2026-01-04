@echo off
set "ROOT=%~dp0.."
set "PY=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not exist "%PY%" set "PY=python"
cd /d "%ROOT%"
echo ========================================
echo  날짜별 백테스트 대시보드 생성
echo ========================================
echo.
"%PY%" -B "src\create_dashboard_from_backtest.py"
echo.
echo 완료! 브라우저에서 web\dashboard.html을 확인하세요.
pause
