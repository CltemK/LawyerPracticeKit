@echo off
chcp 936 >nul
echo ========================================
echo   LegalFileRenamer - Installer
echo ========================================
echo.
echo [1/2] Checking .NET 8 Desktop Runtime...
dotnet --list-runtimes 2>nul | findstr /i "Microsoft.WindowsDesktop.App 8." >nul
if %errorlevel% neq 0 (
    echo.
    echo [!] .NET 8 Desktop Runtime not found.
    echo     Opening download page...
    echo.
    start https://dotnet.microsoft.com/download/dotnet/8.0/runtime
    pause
    exit /b 1
)
echo       ...OK
echo.
echo [2/2] Registering context menu...
set "EXE_PATH=%~dp0LegalFileRenamer.exe"
if not exist "%EXE_PATH%" (
    echo.
    echo [ERROR] LegalFileRenamer.exe not found.
    pause
    exit /b 1
)
reg add "HKCU\Software\Classes\*\shell\LegalFileRenamer" /ve /d "法律文件重命名" /f >nul 2>&1
reg add "HKCU\Software\Classes\*\shell\LegalFileRenamer\command" /ve /d ""%EXE_PATH%" "%%1"" /f >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to write registry.
    pause
    exit /b 1
)
echo       ...OK
echo.
echo ========================================
echo   Install complete!
echo ========================================
echo.
echo   Right-click any file ^> Show more options
echo    to see the menu item.
echo   Run uninstall.bat to remove.
echo.
pause
