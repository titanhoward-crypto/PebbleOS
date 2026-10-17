@echo off
setlocal
rem Builds PebbleOS via WSL by running build_iso.py.
rem Double-click it, or run from a terminal with extra options, e.g.:
rem   build_iso.bat --stage 1
rem   build_iso.bat -o C:\Users\me\Desktop --wsl-distro Debian

cd /d "%~dp0"

set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY (
    where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
    echo ERROR: Python was not found. Install it from https://www.python.org/downloads/
    echo        and tick "Add python.exe to PATH" in the installer.
    goto :end
)

if not exist "build_iso.py" (
    echo ERROR: build_iso.py must be in the same folder as this .bat file.
    goto :end
)

%PY% build_iso.py %*
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (echo Finished OK.) else (echo Build failed with exit code %RC%.)

:end
echo.
pause
endlocal
