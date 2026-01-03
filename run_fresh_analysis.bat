@echo off
cd /d "c:\Users\sksms\Downloads\stock-rs-screener"
echo ========================================
echo  전체 분석 새로 실행
echo ========================================
echo.
C:\Users\sksms\anaconda3\python.exe -B run_full_analysis.py
echo.
echo ========================================
echo  완료! 아무 키나 누르세요...
echo ========================================
pause
