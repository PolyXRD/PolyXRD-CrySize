@echo off
REM Keep exactly TWO deliverables in dist\ :
REM   dist\PolyXRD-CrySize-vX.Y.Z.exe         internal evaluation edition
REM   dist\PolyXRD-CrySize-vX.Y.Z-Setup.exe   registered installer
REM Everything else is deleted: older versions, any fixed-name copy, and the
REM dist\PolyXRD-CrySize\ onedir tree (Inno Setup payload, rebuilt each time).
REM
REM Usage:  tidy_dist.bat          keep the current version, delete the rest
REM         tidy_dist.bat dry      only list what would be deleted
REM         (use "dry", not "/dry": Git-Bash rewrites a single-slash argument
REM          into a Windows path, so "/dry" would silently mean "delete".)
REM
REM NOTE: keep this file pure ASCII (cmd.exe reads .bat in OEM cp936 here).
setlocal
cd /d %~dp0

set DRY=0
if /i "%~1"=="dry" set DRY=1
if /i "%~1"=="--dry" set DRY=1

set PY=D:\Project\XRD\python310\python.exe
if not exist "%PY%" set PY=%USERPROFILE%\.workbuddy\binaries\python\envs\default\Scripts\python.exe
if not exist "%PY%" set PY=python

set VERTMP=%TEMP%\pxrd_crysize_ver.txt
"%PY%" -c "from crysize.version import __version__; print(__version__)" > "%VERTMP%" 2>nul
set VER=
set /p VER=<"%VERTMP%"
del "%VERTMP%" >nul 2>nul

if "%VER%"=="" (
    echo [ERROR] cannot read version from crysize/version.py - nothing deleted.
    endlocal
    exit /b 1
)

set "KEEP1=PolyXRD-CrySize-v%VER%.exe"
set "KEEP2=PolyXRD-CrySize-v%VER%-Setup.exe"

if not exist "dist\%KEEP1%" (
    echo [ERROR] dist\%KEEP1% is missing - nothing deleted.
    endlocal
    exit /b 1
)
if not exist "dist\%KEEP2%" (
    echo [ERROR] dist\%KEEP2% is missing - nothing deleted.
    endlocal
    exit /b 1
)

if "%DRY%"=="1" (
    echo [dry] version %VER% - these would be deleted:
) else (
    echo Tidying dist\ for version %VER% ...
)

set RM=0
for %%F in ("dist\*.exe") do (
    if /i not "%%~nxF"=="%KEEP1%" if /i not "%%~nxF"=="%KEEP2%" (
        echo   - %%~nxF
        if "%DRY%"=="0" del /f /q "%%~fF" >nul 2>nul
        set /a RM+=1
    )
)

REM The onedir tree is the Inno Setup payload, not a deliverable: it is rebuilt
REM by every build_setup run, so it must not stay in dist\ after packaging.
if exist "dist\PolyXRD-CrySize" (
    echo   - PolyXRD-CrySize\  ^(onedir intermediate, Inno payload^)
    if "%DRY%"=="0" (
        rmdir /s /q "dist\PolyXRD-CrySize" >nul 2>nul
        if exist "dist\PolyXRD-CrySize" (
            echo   [WARN] could not remove dist\PolyXRD-CrySize - still present.
        )
    )
    set /a RM+=1
)

if "%DRY%"=="1" (
    echo [dry] %RM% item^(s^) would be removed.
    endlocal
    exit /b 0
)

echo.
echo dist\ now holds:
for %%F in ("dist\*.exe") do echo   %%F
if exist "dist\PolyXRD-CrySize" echo   PolyXRD-CrySize\  ^(should be gone - see WARN above^)
echo Removed %RM% item^(s^).
endlocal
exit /b 0
