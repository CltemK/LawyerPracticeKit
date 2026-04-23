@echo off
chcp 65001 >nul
echo ========================================
echo   LegalFileRenamer - 卸载程序
echo ========================================
echo.
echo 移除右键菜单...
reg delete "HKCU\Software\Classes\*\shell\LegalFileRenamer" /f >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [提示] 注册表项不存在，无需移除
) else (
    echo       ...完成
)
echo.
echo ========================================
echo   卸载完成！
echo ========================================
echo.
pause
