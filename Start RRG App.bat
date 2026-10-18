@echo off
rem Launches the PVR INOX live RRG app and opens it in the browser.
rem If the app is already running, it just opens the browser tab.
title PVR INOX RRG app - keep this window open while using the app
cd /d "%~dp0"

set PORT=8501
set URL=http://localhost:%PORT%

set PY=C:\Users\Lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe
if not exist "%PY%" set PY=python

netstat -ano | findstr /r /c:":%PORT% .*LISTENING" >nul
if %errorlevel%==0 (
    echo App is already running - opening %URL%
    start "" "%URL%"
    exit /b 0
)

echo Starting PVR INOX RRG app...
echo It opens in your browser in a few seconds.
echo Close this window to stop the app.
echo.

rem Streamlit opens the browser itself once the server is ready
"%PY%" -m streamlit run rrg_app.py --server.port %PORT% --server.headless false --browser.serverAddress localhost --browser.gatherUsageStats false

echo.
echo The app stopped. If you see an error above, take a screenshot of it.
pause
