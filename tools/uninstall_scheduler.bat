@echo off
rem Unregisters RRG data refresh scheduled tasks.

echo Removing RRG scheduled tasks...

schtasks /Delete /TN "RRG_Data_Refresh_1545" /F >nul 2>&1
schtasks /Delete /TN "RRG_Data_Refresh_1615" /F >nul 2>&1
schtasks /Delete /TN "RRG_Data_Refresh_1700" /F >nul 2>&1
schtasks /Delete /TN "RRG_Data_Refresh_1830" /F >nul 2>&1

echo RRG scheduled tasks removed.
