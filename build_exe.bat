@echo off
REM Build PolyXRD CrySize as a single-file portable exe (INTERNAL edition).
REM Dependencies (PySide6/numpy/scipy/matplotlib) are preinstalled in
REM D:\Project\XRD\python310, same environment as the rest of the PolyXRD family.
REM Outputs:
REM   dist\PolyXRD-CrySize-vX.Y.Z.exe   <- versioned, the internal evaluation edition
REM No fixed-name copy: dist\ must hold exactly two deliverables, this exe and
REM the Setup installer. tidy_dist.bat enforces that.
REM The version is read from crysize\version.py; the spec uses the same value.
cd /d %~dp0
set PY=D:\Project\XRD\python310\python.exe
if not exist "%PY%" set PY=python

for /f "delims=" %%v in ('%PY% -c "from crysize.version import __version__; print(__version__)"') do set VER=%%v

echo Building PolyXRD CrySize v%VER% (internal edition) ...
"%PY%" -m PyInstaller --noconfirm --clean PolyXRD-CrySize.spec
if errorlevel 1 goto :fail

echo.
echo Done:
echo   dist\PolyXRD-CrySize-v%VER%.exe
exit /b 0

:fail
echo.
echo BUILD FAILED
exit /b 1
