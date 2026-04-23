@echo off
chcp 65001 >nul
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
cd /d "%~dp0"
rc resource.rc
if %errorlevel% neq 0 (echo RC 编译失败 & pause & exit /b 1)
cl /O2 /W3 /utf-8 /DUNICODE /D_UNICODE main.c resource.res /link /SUBSYSTEM:WINDOWS shlwapi.lib user32.lib gdi32.lib shell32.lib /OUT:LegalFileRenamer.exe
if %errorlevel% neq 0 (echo CL 编译失败 & pause & exit /b 1)
del /q *.obj *.res >nul 2>&1
echo.
echo ========================================
echo   构建成功！
echo ========================================
dir LegalFileRenamer.exe
pause
