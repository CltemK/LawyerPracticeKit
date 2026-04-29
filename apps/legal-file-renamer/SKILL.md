# legal-file-renamer

## Description

法律文件重命名工具。Windows 右键菜单集成，通过 GUI 对法律文件进行规范化命名，支持自动解析已格式化的文件名。纯 C + Win32 API 实现，零依赖单文件（~150KB）。

**核心功能：**
- 右键菜单一键启动重命名对话框
- 自动填充当日日期，支持手动修改
- 文件类型选择：客户文件 / 律师文件（初稿/修订/终稿）
- 实时预览新文件名，自动缩放字体适配长名称
- 自动解析已格式化的文件名（如 `20260418_【客户】_采购合同_V1.pdf`），回填各字段
- 一键定稿：律师文件快速转为终稿
- 日期校验（含闰年）、非法字符检查、版本号格式校验
- 重命名后通知资源管理器刷新

## Use Cases

在 Windows 资源管理器中右键点击任意文件，选择"法律文件重命名"，弹出对话框填写日期、类型、名称、版本号，预览确认后执行重命名。

**命名格式：** `{日期}_{文件类型}_{文件名称}_{版本号}.{扩展名}`

**示例：**
- `20260418_【客户】_采购合同_V1.pdf`
- `20260418_【初稿】_劳动合同_V1.docx`
- `20260418_【修订V2】_协议_V1.1.xlsx`
- `20260418_【终稿】_协议_V2.pdf`

## Installation

### 方式一：下载编译好的 exe

从 Release 页面下载 `LegalFileRenamer.exe`，与 `install.bat`、`install.ps1` 放在同一目录，双击 `install.bat` 即可注册右键菜单。

### 方式二：从源码编译

需要 Visual Studio 2022（含 C++ 桌面开发工作负载）：

```bat
cd skills\legal-file-renamer
build.bat
```

编译产物：`LegalFileRenamer.exe`（~150KB，零依赖）

### 注册右键菜单

```bat
install.bat
```

### 卸载

```bat
uninstall.bat
```

## Files

| 文件 | 说明 |
|------|------|
| `main.c` | 主程序源码（~840 行，C + Win32 API） |
| `resource.h` / `resource.rc` / `app.manifest` | 资源文件和 DPI 感知清单 |
| `build.bat` | 编译脚本（自动查找 VS 安装路径） |
| `install.bat` / `install.ps1` | 安装脚本（注册右键菜单 + 恢复经典菜单） |
| `uninstall.bat` / `uninstall.ps1` | 卸载脚本 |
| `SPEC.md` | 功能规格说明书 |

## Technical Notes

- **框架**：纯 C + Win32 API，无 .NET / MFC 依赖
- **编码**：Unicode (UTF-16)，完整支持中文文件名
- **注册表**：写入 `HKCU\Software\Classes\*\shell\LegalFileRenamer`（用户级，无需管理员权限）
- **安装脚本**：通过 PowerShell 生成 .reg 文件导入，避免 `chcp 65001` 编码问题和 `*` 通配符问题
- **兼容性**：Windows 10/11，支持高 DPI 显示
