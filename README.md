# LawyerPracticeKit

律师实践工具包 — 法律工作中的实用工具集合。

## 目录结构

```
LawyerPracticeKit/
├── skills/                      # AI 辅助脚本（需 AI 编程环境运行）
│   └── court-doc-downloader/    # 法院送达文书自动下载与归档
├── apps/                        # 独立桌面应用程序（可直接运行）
│   ├── legal-file-renamer/      # 法律文件规范化重命名（C / Win32）
│   └── wechat-screenshot-organizer/  # 微信截图整理工具（Python / PyQt5）
├── shared/                      # 公共模块
├── README.md
├── .gitignore
└── LICENSE
```

## Skills — AI 辅助脚本

| Skill | 说明 | 语言 |
|-------|------|------|
| [court-doc-downloader](skills/court-doc-downloader/SKILL.md) | 法院送达文书自动下载、解析与归档（支持飞书云空间 + 日历排期） | Python |

```bash
# 安装依赖
pip install pdfplumber playwright
playwright install chromium

# 使用
python skills/court-doc-downloader/court_doc_downloader.py "<法院送达链接>"
```

详见 [SKILL.md](skills/court-doc-downloader/SKILL.md)。

## Apps — 独立桌面应用

### legal-file-renamer（法律文件重命名）

Windows 桌面工具，右键菜单一键规范化法律文件名。C + Win32 API，零依赖。

```bat
cd apps\legal-file-renamer
build.bat          :: 编译（需 Visual Studio 2022）
install.bat        :: 注册右键菜单
```

详见 [SKILL.md](apps/legal-file-renamer/SKILL.md)。

### wechat-screenshot-organizer（微信截图整理）

将微信聊天截图自动识别时间、整理为 Word 文档。Python + PyQt5。

```bash
cd apps/wechat-screenshot-organizer
pip install -r requirements.txt
python main.py
```

## 兼容环境

Skills 目录中的每个工具都有 `SKILL.md` 指令文件，可在以下 AI 编程环境中使用：

| 环境 | 使用方式 |
|------|----------|
| **WorkBuddy** | 将 `skills/<name>/` 复制到 `~/.workbuddy/skills/` |
| **Claude Code** | 将 `SKILL.md` 放入 `.claude/commands/` |
| **Cursor** | 放入 `.cursor/rules/` |
| **Windsurf** | 放入 `.windsurf/rules/` |
| **纯命令行** | 直接运行脚本 |

Apps 目录中的应用为独立程序，无需 AI 环境即可使用。

## License

[MIT](LICENSE)
