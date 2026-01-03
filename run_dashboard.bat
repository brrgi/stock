@echo off
cd /d "c:\Users\sksms\Downloads\stock-rs-screener"
del /Q dashboard.html 2>NUL
echo ========================================
echo  Dashboard.html 생성
echo ========================================
echo.
C:\Users\sksms\anaconda3\python.exe -B create_current_dashboard.py
echo.
echo ========================================
echo  완료!
echo ========================================
pause
