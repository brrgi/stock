@echo off
cd /d "c:\Users\sksms\Downloads\stock-rs-screener"
del /Q dashboard.html 2>NUL
echo ========================================
echo  대시보드 재생성
echo ========================================
echo.
C:\Users\sksms\anaconda3\python.exe -B regenerate_now.py
echo.
pause
