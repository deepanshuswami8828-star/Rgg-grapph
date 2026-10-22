@echo off
rem Batch wrapper for RRG data refresh
cd /d "%~dp0\.."

set PY=C:\Users\Lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe
if not exist "%PY%" set PY=python

"%PY%" tools\refresh_data.py %*
exit /b %errorlevel%
