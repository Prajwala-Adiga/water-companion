@echo off
setlocal
cd /d "%~dp0"
set "BUILD_TEMP=%CD%\.build-temp"
if not exist "%BUILD_TEMP%" mkdir "%BUILD_TEMP%"
set "TEMP=%BUILD_TEMP%"
set "TMP=%BUILD_TEMP%"

if not exist ".venv\Scripts\python.exe" (
  echo Run SETUP.bat first.
  pause
  exit /b 1
)

.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
if errorlevel 1 goto fail
.venv\Scripts\python.exe prepare_release.py
if errorlevel 1 goto fail
set /p APP_VERSION=<VERSION
if not defined APP_VERSION goto fail
.venv\Scripts\python.exe make_icon.py
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m unittest -v
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --onedir --name FahadhWaterCompanion --icon assets\fahadh.ico --version-file version_info.txt --add-data "assets;assets" app.py
if errorlevel 1 goto fail

if not exist release mkdir release
if exist "release\FahadhWaterCompanion-Portable-%APP_VERSION%.zip" del /q "release\FahadhWaterCompanion-Portable-%APP_VERSION%.zip"
tar.exe -a -c -f "release\FahadhWaterCompanion-Portable-%APP_VERSION%.zip" -C dist FahadhWaterCompanion
if errorlevel 1 goto fail

set "ISCC=iscc"
where iscc >nul 2>&1
if not errorlevel 1 goto build_installer
set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%USERPROFILE%\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" goto no_installer

:build_installer
"%ISCC%" /DAppVersion=%APP_VERSION% installer.iss
if errorlevel 1 goto fail
goto release_done

:no_installer
echo Portable ZIP created. Install Inno Setup 6 to also build the installer.

:release_done

if not exist "release\FahadhWaterCompanion-Portable-%APP_VERSION%.zip" goto fail
echo Release %APP_VERSION% files are ready in the release folder.
if exist "%BUILD_TEMP%" rmdir /s /q "%BUILD_TEMP%"
pause
exit /b 0

:fail
if exist "%BUILD_TEMP%" rmdir /s /q "%BUILD_TEMP%"
echo Release build failed. Read the error above.
pause
exit /b 1
