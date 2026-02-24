<div align="center">

# Project Start Skill

[![许可协议](https://img.shields.io/badge/许可协议-Apache%202.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7+-brightgreen.svg)](https://www.python.org/downloads/)
[![Claude Skills](https://img.shields.io/badge/Claude-Skills-purple.svg)](https://skills.sh/)

**基于任意项目/模板创建新项目：检索 → 理解 → 用户确认 → 执行**

</div>

---

## 概述

**Project Start Skill** 用于自动化初始化和定制「基于 X 项目/模板 创建 Y 项目」的场景。适用于 Java、Python、Node 等任意技术栈。

**核心原则**：**必须先展示修改计划并得到用户明确确认，再执行**。禁止跳过确认直接修改文件。

### 适用场景

- 「基于 LightRAG 初始化 SuperRAG」（Python）
- 「基于 ContiNew Admin 创建 MyCompany Admin」（Java）
- 「基于 RuoYi 初始化 myproject」（Java）
- 任意「基于 X 创建 Y」的项目初始化请求

### 强制流程

1. **检索与理解**：有脚本（Java/Maven）则运行 `analyze_project`，无脚本则 Agent 手动探索
2. **生成计划**：输出修改清单（checklist）
3. **用户确认**：向用户展示计划，**显式询问**是否确认，等待肯定答复
4. **执行**：仅当用户确认后，执行复制、重命名、替换等操作

### 预设框架（可选）

| 框架 | 品牌 | 包路径 |
|------|------|--------|
| ContiNew Admin | continew | top.continew.admin |
| RuoYi | ruoyi | com.ruoyi |

预设可加速推断，但**不改变主流程**：仍需展示计划并等待确认。

## 安装

将 `project-start-skill` 目录放入 `.cursor/skills/` 即可使用。

## 快速开始

### 通用用法（任何项目类型）

向 Claude 描述需求，例如：

> "基于 LightRAG-main 初始化一个名为 SuperRAG 的新项目"
> "基于 ContiNew Admin 创建 MyCompany Admin，包名为 com.mycompany.admin"

**重要**：Claude 会先探索项目、生成修改清单，**向您展示计划并询问确认**。请确认后再执行。

### Java 项目（有脚本）

1. 运行分析脚本：
```bash
cd .cursor/skills/project-start-skill/scripts
python analyze_project.py --path /path/to/project --brand-new mycompany --package-new com.mycompany --output report
```

2. **查看并确认**生成的 `report-checklist.md` 内容
3. 确认后执行：
```bash
python init_project.py --config report-config.yaml --project-root /path/to/project --dry-run  # 建议先预览
python init_project.py --config report-config.yaml --project-root /path/to/project
```

### 交互模式（Java 预设）

```bash
python scripts/init_project.py --interactive
python scripts/init_project.py --interactive --framework ruoyi
```

即使使用预设，**仍应展示将修改的内容并取得用户认可**后再执行。

## 项目结构

```
project-start-skill/
├── SKILL.md                    # 主技能文档（含前置规则、流程、确认规范）
├── README.md                   # 本文件
├── scripts/
│   ├── analyze_project.py     # Java/Maven 项目分析（输出 config/report/checklist）
│   ├── init_project.py         # 初始化脚本
│   └── create_project.py       # 从模板创建
├── references/
│   └── replacement-rules.md    # ContiNew 与 RuoYi 替换规则
└── assets/
    ├── config-template.yaml    # 配置模板
    └── framework-presets.yaml  # 框架预设（可选快捷方式）
```

## 文档

- **[SKILL.md](SKILL.md)** - 完整技能文档（前置规则、确认步骤、无脚本发现等）
- **[替换规则](references/replacement-rules.md)** - ContiNew 与 RuoYi 替换模式

## 系统要求

- Python 3.7+
- PyYAML：`pip install pyyaml`

## 重要提示

> **运行初始化前务必备份您的项目！**

- **确认不可跳过**：无论何种项目，均须展示计划并等待用户确认后再执行
- 先备份：创建原始项目的备份
- cap_old/cap_new：用于 PascalCase 替换；preserve 可保留 Maven 依赖等
- 模块依赖：移除模块前验证依赖关系

## 相关链接

- [ContiNew Admin](https://github.com/continew-org/continew-admin)
- [RuoYi](https://gitee.com/y_project/RuoYi)
