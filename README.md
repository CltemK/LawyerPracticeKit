# LawyerPracticeKit

律师实践工具包 — 通用 AI 辅助编程环境均可使用的法律工具集合。

> **不限于 WorkBuddy。** 本仓库中的每个 Skill 均为独立脚本 / 工具，可在 **WorkBuddy / Claude Code / Cursor / Windsurf / OpenCode / Cline** 等任意 AI 编程环境中使用。

## Skills

| Skill | 说明 | 语言 | 状态 |
|-------|------|------|------|
| [court-doc-downloader](skills/court-doc-downloader/SKILL.md) | 法院送达文书自动下载、解析与归档（支持飞书云空间 + 日历排期） | Python | ✅ 已上线 |
| [legal-file-renamer](skills/legal-file-renamer/SKILL.md) | 法律文件规范化重命名工具（Windows 右键菜单集成） | C / Win32 | ✅ 已上线 |

## 结构

```
LawyerPracticeKit/
├── skills/                      # 各 skill 独立目录
│   ├── court-doc-downloader/    # 法院文档下载工具
│   │   ├── SKILL.md             # Skill 说明与使用指南
│   │   ├── court_doc_downloader.py
│   │   └── rmfyalk_downloader.py
│   └── legal-file-renamer/      # 法律文件重命名工具
│       ├── SKILL.md             # Skill 说明与使用指南
│       ├── main.c               # 主程序源码（C + Win32 API）
│       ├── build.bat            # 编译脚本
│       ├── install.bat/ps1      # 安装脚本
│       ├── uninstall.bat/ps1    # 卸载脚本
│       └── SPEC.md              # 功能规格说明书
├── shared/                      # 公共模块（供多 skill 复用）
├── README.md
├── .gitignore
└── LICENSE
```

## 各 Skill 快速使用

### court-doc-downloader（法院文档下载）

```bash
# 安装依赖
pip install pdfplumber playwright
playwright install chromium

# 使用
python skills/court-doc-downloader/court_doc_downloader.py "<法院送达链接>"
```

详见 [SKILL.md](skills/court-doc-downloader/SKILL.md)。

### legal-file-renamer（法律文件重命名）

Windows 桌面工具，需 Visual Studio 2022 编译：

```bat
cd skills\legal-file-renamer
build.bat          :: 编译
install.bat        :: 注册右键菜单
```

或从 Release 下载编译好的 exe 直接使用。详见 [SKILL.md](skills/legal-file-renamer/SKILL.md)。

## 兼容环境

本仓库的每个 Skill 都是独立工具 + `SKILL.md` 指令文件，不依赖特定平台的私有 API，因此可以在以下所有环境中使用：

| 环境 | 使用方式 |
|------|----------|
| **WorkBuddy** | 将 `skills/<name>/` 复制到 `~/.workbuddy/skills/` 即可自动识别 |
| **Claude Code** | 将 `SKILL.md` 放入 `.claude/commands/` 或项目 `CLAUDE.md` 引用 |
| **Cursor** | 放入 `.cursor/rules/` 或作为 `.md` 规则文件引用 |
| **Windsurf** | 放入 `.windsurf/rules/` |
| **OpenCode / Cline** | 将 `SKILL.md` 内容粘贴为自定义指令 / system prompt 片段 |
| **纯命令行** | 直接运行脚本，无需 AI 环境 |

## 贡献

欢迎提交 Issue 和 Pull Request。

## License

[MIT](LICENSE)
