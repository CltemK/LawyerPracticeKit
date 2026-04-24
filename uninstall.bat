@echo off
chcp 65001 >nul
echo ========================================
echo   LegalFileRenamer - 卸载程序
echo ========================================
echo.

echo [1/2] 移除右键菜单...
reg delete "HKCU\Software\Classes\*\shell\LegalFileRenamer" /f >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [提示] 注册表项不存在，无需移除
) else (
    echo       ...完成
)
echo.

echo [2/2] 恢复 Win11 新版右键菜单...
reg delete "HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}" /f >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [提示] 经典菜单注册表项不存在，无需恢复
) else (
    echo       ...完成
)
echo.

echo ========================================
echo   卸载完成！
echo ========================================
echo.
echo   如需重启资源管理器使设置生效：
echo   任务管理器 → 找到"Windows 资源管理器" → 右键重启
echo.
pause
