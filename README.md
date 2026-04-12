# LawyerPracticeKit

律师实践工具包 — 基于 WorkBuddy Skill 体系的专业法律工具集合。

## Skills

| Skill | 说明 | 状态 |
|-------|------|------|
| [court-doc-downloader](skills/court-doc-downloader/SKILL.md) | 法院送达文书自动下载、解析与归档（支持飞书云空间 + 日历排期） | ✅ 已上线 |

## 结构

```
LawyerPracticeKit/
├── skills/                    # 各 skill 独立目录
│   └── court-doc-downloader/  # 法院文档下载工具
│       ├── SKILL.md
│       └── court_doc_downloader.py
├── shared/                    # 公共模块（供多 skill 复用）
├── README.md
├── .gitignore
└── LICENSE
```

## 快速开始

每个 `skills/<name>/` 目录都是一个独立、可安装的 WorkBuddy Skill，包含：
- **SKILL.md** — Skill 说明与使用指南
- **Python 脚本 / 其他代码** — 核心逻辑

### 安装单个 Skill

将目标目录复制到你的 WorkBuddy skills 目录即可：
```bash
cp -r skills/court-doc-downloader ~/.workbuddy/skills/
```

## 贡献

欢迎提交 Issue 和 Pull Request。
