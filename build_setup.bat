@echo off
REM Build PolyXRD CrySize REGISTERED EDITION:
REM   1. PyInstaller onedir build from PolyXRD-CrySize-Setup.spec
REM      -> dist\PolyXRD-CrySize\PolyXRD-CrySize.exe (+ support files)
REM   2. Inno Setup installer from installer\PolyXRD-CrySize.iss
REM      -> dist\PolyXRD-CrySize-vX.Y.Z-Setup.exe
REM Version is read from crysize/version.py (single source of truth).
REM Ends with tidy_dist.bat: dist\ keeps only the two deliverables.
REM NOTE: keep comments ASCII-only to stay safe under any cmd codepage.
cd /d %~dp0
set PY=D:\Project\XRD\python310\python.exe
if not exist "%PY%" set PY=python
set ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" set ISCC=ISCC.exe

for /f "delims=" %%v in ('%PY% -c "from crysize.version import __version__; print(__version__)"') do set VER=%%v

echo [1/2] Building onedir (registered edition) v%VER% ...
"%PY%" -m PyInstaller --noconfirm --clean PolyXRD-CrySize-Setup.spec
if errorlevel 1 goto :fail
if not exist "dist\PolyXRD-CrySize\PolyXRD-CrySize.exe" goto :fail

echo [2/2] Building installer with Inno Setup ...
"%ISCC%" /DAPP_VER=v%VER% installer\PolyXRD-CrySize.iss
if errorlevel 1 goto :fail

call tidy_dist.bat
echo.
echo Done:
echo   dist\PolyXRD-CrySize-v%VER%.exe                  (internal evaluation edition)
echo   dist\PolyXRD-CrySize-v%VER%-Setup.exe            (registered installer)
exit /b 0

:fail
echo.
echo BUILD FAILED
exit /b 1
