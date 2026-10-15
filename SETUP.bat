@echo off
setlocal
cd /d "%~dp0"
py -3.12 --version >nul 2>&1
if errorlevel 1 (
  echo Please install Python 3.12 for Windows from https://www.python.org/downloads/windows/
  echo Include the Python launcher during installation, then run SETUP.bat again.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" py -3.12 -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo Setup complete. Double-click START.bat to meet your companion.
pause
exit /b 0
:fail
echo Setup failed. Check the message above and your internet connection.
pause
exit /b 1
