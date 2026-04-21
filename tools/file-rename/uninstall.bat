@echo off
chcp 936 >nul
echo ========================================
echo   LegalFileRenamer - Uninstaller
echo ========================================
echo.
echo Removing context menu entry...
reg delete "HKCU\Software\Classes\*\shell\LegalFileRenamer" /f
if %errorlevel% neq 0 (
    echo.
    echo [INFO] Registry entry not found.
) else (
    echo.
    echo ========================================
    echo   Uninstall complete!
    echo ========================================
)
echo.
pause
