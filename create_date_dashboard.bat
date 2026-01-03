@echo off
cd /d "c:\Users\sksms\Downloads\stock-rs-screener"
echo ========================================
echo  날짜별 백테스트 대시보드 생성
echo ========================================
echo.
C:\Users\sksms\anaconda3\python.exe create_dashboard_from_backtest.py
echo.
echo 완료! 브라우저에서 dashboard.html을 확인하세요.
pause
