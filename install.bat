@echo off
chcp 65001 >nul
echo ========================================
echo   LegalFileRenamer - 安装程序
echo ========================================
echo.
echo [1/2] 注册右键菜单...
set "EXE_PATH=%~dp0LegalFileRenamer.exe"
if not exist "%EXE_PATH%" (
    echo.
    echo [错误] 未找到 LegalFileRenamer.exe
    echo        请确认 exe 文件与此脚本在同一目录
    pause
    exit /b 1
)
reg add "HKCU\Software\Classes\*\shell\LegalFileRenamer" /ve /d "法律文件重命名" /f >nul 2>&1
reg add "HKCU\Software\Classes\*\shell\LegalFileRenamer\command" /ve /d "\"%EXE_PATH%\" \"%%1\"" /f >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [错误] 注册表写入失败
    pause
    exit /b 1
)
echo       ...完成
echo.
echo [2/2] 写入注册表文件...
> "%~dp0register.reg" (
    echo Windows Registry Editor Version 5.00
    echo.
    echo [HKEY_CURRENT_USER\Software\Classes\*\shell\LegalFileRenamer]
    echo @="法律文件重命名"
    echo.
    echo [HKEY_CURRENT_USER\Software\Classes\*\shell\LegalFileRenamer\command]
    echo @="\"%EXE_PATH%\" \"%%1\""
)
echo       ...完成
echo.
echo ========================================
echo   安装成功！
echo ========================================
echo.
echo   右键点击任意文件 即可看到菜单项
echo   运行 uninstall.bat 可卸载
echo.
pause
