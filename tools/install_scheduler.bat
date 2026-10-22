@echo off
rem Registers automatic weekday scheduled tasks for RRG data refresh using schtasks.
rem Times are set for IST (Indian Standard Time):
rem   - 15:45 IST (15 minutes after market close)
rem   - 16:15 IST (retry 1)
rem   - 17:00 IST (retry 2)
rem   - 18:30 IST (retry 3)
rem NOTE: If your PC is in a different timezone, adjust the times below to your local time equivalent.

set BAT_PATH=%~dp0refresh_data.bat

echo Registering RRG scheduled tasks...

schtasks /Create /TN "RRG_Data_Refresh_1545" /TR "\"%BAT_PATH%\"" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 15:45 /F
schtasks /Create /TN "RRG_Data_Refresh_1615" /TR "\"%BAT_PATH%\"" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 16:15 /F
schtasks /Create /TN "RRG_Data_Refresh_1700" /TR "\"%BAT_PATH%\"" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 17:00 /F
schtasks /Create /TN "RRG_Data_Refresh_1830" /TR "\"%BAT_PATH%\"" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 18:30 /F

echo.
echo ======================================================================
echo RRG Scheduled Tasks Registered Successfully!
echo To verify, run: schtasks /Query /TN "RRG_Data_Refresh_1545"
echo To uninstall anytime, run: tools\uninstall_scheduler.bat
echo ======================================================================
