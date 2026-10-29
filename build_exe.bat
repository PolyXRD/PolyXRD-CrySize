@echo off
REM Build PolyXRD CrySize as a single-file portable exe (INTERNAL edition).
REM Dependencies (PySide6/numpy/scipy/matplotlib) are preinstalled in
REM D:\Project\XRD\python310, same environment as the rest of the PolyXRD family.
REM Outputs:
REM   dist\PolyXRD-CrySize-vX.Y.Z.exe   <- versioned
REM   dist\PolyXRD-CrySize.exe          <- fixed-name copy (GitHub Release asset)
REM The version is read from crysize\version.py; the spec uses the same value.
cd /d %~dp0
set PY=D:\Project\XRD\python310\python.exe
if not exist "%PY%" set PY=python

for /f "delims=" %%v in ('%PY% -c "from crysize.version import __version__; print(__version__)"') do set VER=%%v

echo Building PolyXRD CrySize v%VER% (internal edition) ...
"%PY%" -m PyInstaller --noconfirm --clean PolyXRD-CrySize.spec
if errorlevel 1 goto :fail

if exist "dist\PolyXRD-CrySize-v%VER%.exe" copy /Y "dist\PolyXRD-CrySize-v%VER%.exe" "dist\PolyXRD-CrySize.exe"
echo.
echo Done:
echo   dist\PolyXRD-CrySize-v%VER%.exe
if exist "dist\PolyXRD-CrySize.exe" echo   dist\PolyXRD-CrySize.exe
exit /b 0

:fail
echo.
echo BUILD FAILED
exit /b 1
