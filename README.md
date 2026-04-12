# LawyerPracticeKit

律师实践工具包 — 通用 AI 辅助编程环境均可使用的法律工具集合。

> **不限于 WorkBuddy。** 本仓库中的每个 Skill 均为独立的 Python 脚本 / 命令行工具，可在 **WorkBuddy / Claude Code / Cursor / Windsurf / OpenCode / Cline** 等任意 AI 编程环境中使用。

## Skills

| Skill | 说明 | 状态 |
|-------|------|------|
| [court-doc-downloader](skills/court-doc-downloader/SKILL.md) | 法院送达文书自动下载、解析与归档（支持飞书云空间 + 日历排期） | ✅ 已上线 |

## 结构

```
LawyerPracticeKit/
├── skills/                    # 各 skill 独立目录
│   └── court-doc-downloader/  # 法院文档下载工具
│       ├── SKILL.md           # Skill 说明与使用指南
│       └── court_doc_downloader.py  # 核心脚本（独立可执行）
├── shared/                    # 公共模块（供多 skill 复用）
├── README.md
├── .gitignore
└── LICENSE
```

## 兼容环境

本仓库的每个 Skill 都是 **独立 Python 脚本 + `SKILL.md` 指令文件**，不依赖特定平台的私有 API，因此可以在以下所有环境中使用：

| 环境 | 使用方式 |
|------|----------|
| **WorkBuddy** | 将 `skills/<name>/` 复制到 `~/.workbuddy/skills/` 即可自动识别 |
| **Claude Code** | 将 `SKILL.md` 放入 `.claude/commands/` 或 `.cursor/rules/`；AI 会按指令调用脚本 |
| **Cursor** | 同上，放入 `.cursor/rules/` 或作为 `.md` 规则文件引用 |
| **Windsurf** | 放入 `.windsurf/rules/` |
| **OpenCode / Cline** | 将 `SKILL.md` 内容粘贴为自定义指令 / system prompt 片段 |
| **纯命令行** | 直接 `python court_doc_downloader.py <URL>` 运行，无需 AI 环境 |

## 快速开始

### 1️⃣ 安装依赖

```bash
pip install pdfplumber playwright
playwright install chromium
```

还需要安装 [lark-cli](https://github.com/larksuite/lark-cli)（飞书操作）并完成授权登录：
```bash
npm install -g @anthropic-ai/lark-cli   # 或对应包名
lark-cli auth login
```

### 2️⃣ 配置环境变量

```bash
# 必填：飞书团队日历 ID（传票自动创建开庭日程）
export COURT_TEAM_CALENDAR_ID="<你的日历ID>"

# 可选：飞书上传目标文件夹 token（默认上传到根目录）
export COURT_FEISHU_FOLDER_TOKEN="<folder_token>"

# 可选：本地备份目录（上传失败时使用）
export COURT_OUTPUT_DIR="./court_documents"
```

### 3️⃣ 使用

```bash
# 基本用法：下载 → 解析 → 上传飞书 → 创建日历
python skills/court-doc-downloader/court_doc_downloader.py "<法院送达链接>"

# 指定父文件夹
python skills/court-doc-downloader/court_doc_downloader.py "<链接>" --parent-folder "<folder_token>"

# 跳过日历创建
python skills/court-doc-downloader/court_doc_downloader.py "<链接>" --skip-calendar

# 只下载指定文件（按序号）
python skills/court-doc-downloader/court_doc_downloader.py "<链接>" --files "1,3,5"
```

### 各环境安装方式

<details>
<summary><b>WorkBuddy</b></summary>

```bash
cp -r skills/court-doc-downloader ~/.workbuddy/skills/
```
重启会话后自动识别。

</details>

<details>
<summary><b>Claude Code</b></summary>

```bash
# 方式一：作为 Claude Code 自定义命令
mkdir -p .claude/commands
ln -s $(pwd)/skills/court-doc-downloader/SKILL.md .claude/commands/court-doc.md

# 方式二：放入 CLAUDE.md 引用
echo "## 法院文档下载\n参见 skills/court-doc-downloader/SKILL.md" >> CLAUDE.md
```
然后在对话中输入 `/court-doc <链接>` 或直接描述需求即可。

</details>

<details>
<summary><b>Cursor / Windsurf</b></summary>

```bash
# Cursor Rules
mkdir -p .cursor/rules
cp skills/court-doc-downloader/SKILL.md .cursor/rules/court-doc-downloader.md

# Windsurf Rules
mkdir -p .windsurf/rules
cp skills/court-doc-downloader/SKILL.md .windsurf/rules/court-doc-downloader.md
```
AI 在编码时会自动参考规则文件中的指令。

</details>

<details>
<summary><b>OpenCode / Cline（VS Code 插件）</b></summary>

将 `skills/cort-doc-downloader/SKILL.md` 的内容添加到：
- **OpenCode**: 自定义 System Prompt
- **Cline**: VS Code 设置中的 Cline Custom Instructions

或直接在对话中粘贴 SKILL.md 内容作为上下文。

</details>

## 贡献

欢迎提交 Issue 和 Pull Request。

## License

[MIT](LICENSE)
