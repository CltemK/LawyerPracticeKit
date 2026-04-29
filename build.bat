@echo off
chcp 65001 >nul
cd /d "%~dp0"

rem --- Locate Visual Studio ---
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if exist "%VSWHERE%" (
    for /f "delims=" %%i in ('"%VSWHERE%" -latest -property installationPath') do set "VSROOT=%%i"
) else (
    rem Fallback to default path
    set "VSROOT=C:\Program Files\Microsoft Visual Studio\2022\Community"
)
if not exist "%VSROOT%\VC\Auxiliary\Build\vcvars64.bat" (
    echo [ERROR] Visual Studio not found
    pause
    exit /b 1
)
call "%VSROOT%\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1

rc resource.rc
if %errorlevel% neq 0 (echo RC compile failed & pause & exit /b 1)
cl /O2 /W3 /utf-8 /DUNICODE /D_UNICODE main.c resource.res /link /SUBSYSTEM:WINDOWS shlwapi.lib user32.lib gdi32.lib shell32.lib /OUT:LegalFileRenamer.exe
if %errorlevel% neq 0 (echo CL compile failed & pause & exit /b 1)
del /q *.obj *.res >nul 2>&1
echo.
echo Build succeeded!
dir LegalFileRenamer.exe
pause
