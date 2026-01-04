@echo off
set "ROOT=%~dp0.."
set "PY=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not exist "%PY%" set "PY=python"
cd /d "%ROOT%"
echo ========================================
echo  전체 분석 새로 실행
echo ========================================
echo.
"%PY%" -B "src\run_full_analysis.py"
echo.
echo ========================================
echo  완료! 아무 키나 누르세요...
echo ========================================
pause
