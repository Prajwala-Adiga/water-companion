@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Run SETUP.bat first.
  pause
  exit /b 1
)

.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
if errorlevel 1 goto fail
.venv\Scripts\python.exe make_icon.py
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m unittest -v
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --onedir --name FahadhWaterCompanion --icon assets\fahadh.ico --version-file version_info.txt --add-data "assets;assets" app.py
if errorlevel 1 goto fail

if not exist release mkdir release
powershell -NoProfile -Command "Compress-Archive -Path 'dist\FahadhWaterCompanion' -DestinationPath 'release\FahadhWaterCompanion-Portable-1.0.0.zip' -Force"
if errorlevel 1 goto fail

set "ISCC=iscc"
where iscc >nul 2>&1
if not errorlevel 1 goto build_installer
set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" goto no_installer

:build_installer
"%ISCC%" installer.iss
if errorlevel 1 goto fail
goto release_done

:no_installer
echo Portable ZIP created. Install Inno Setup 6 to also build the installer.

:release_done

echo Release files are ready in the release folder.
pause
exit /b 0

:fail
echo Release build failed. Read the error above.
pause
exit /b 1
