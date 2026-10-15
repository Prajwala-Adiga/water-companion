@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run SETUP.bat first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m pip install "pyinstaller>=6.11,<7"
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --onedir --name FahadhWaterCompanion --add-data "assets;assets" app.py
if errorlevel 1 goto fail
echo Built! Open dist\FahadhWaterCompanion\FahadhWaterCompanion.exe
echo Keep the ENTIRE FahadhWaterCompanion folder together, including _internal.
explorer "dist\FahadhWaterCompanion"
pause
exit /b 0
:fail
echo Build failed. Read the error above.
pause
exit /b 1
