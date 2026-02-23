<div align="center">

<img src="logo.png" alt="ContiNew Start Skill Logo" width="120" height="120">

# ContiNew Start Skill

[![版本](https://img.shields.io/badge/版本-1.1.0-blue.svg)](https://github.com/itxaiohanglover/continew-start-skill)
[![许可协议](https://img.shields.io/badge/许可协议-Apache%202.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7+-brightgreen.svg)](https://www.python.org/downloads/)
[![Claude Skills](https://img.shields.io/badge/Claude-Skills-purple.svg)](https://skills.sh/)

**自动化 ContiNew Admin 二次初始化，支持安全预演与模块联动清理**

</div>

---

## 概述

**ContiNew Start Skill** 是一个面向 Claude Code 的初始化技能，用于将 [ContiNew Admin](https://github.com/continew-org/continew-admin) 快速改造成你的业务工程。

它覆盖：品牌替换、包路径替换、目录重命名、可选模块移除、元数据更新，并提供 `dry-run`、备份与失败回滚。

## 功能特性

- 🚀 快速初始化：几分钟完成基础改造
- 🎨 品牌定制：`continew` -> 自定义品牌
- 📦 包路径重构：`top.continew.admin` -> 自定义包名
- 🗂️ 目录重命名：按配置批量改模块目录
- ⚙️ 模块移除：删除模块并联动清理 `pom.xml` 依赖与聚合项
- 🧪 干跑预演：`--dry-run` 先看变更再落盘
- 🛟 安全机制：支持备份与失败回滚
- 🛡️ 保护规则：避免误改 `top.continew.starter` / `continew-starter`

## 安装

### 方法 1：Claude Skills CLI（推荐）

```bash
npx skills add itxaiohanglover/continew-start-skill
```

### 方法 2：本地路径安装

```bash
npx skills add path/to/continew-start-skill
```

## 快速开始

### 方式 A：让 Claude 直接执行

> "用 continew-start-skill 初始化项目，brand=mycompany，package=com.mycompany.admin"

### 方式 B：配置文件 + 脚本

1. 复制 `assets/config-template.yaml`
2. 按需修改配置
3. 执行初始化

```bash
python scripts/init_project.py --config my-config.yaml
```

先预演（不写入）：

```bash
python scripts/init_project.py --config my-config.yaml --dry-run
```

### Advanced CLI Options

```bash
# Strict mode: treat warnings as failure
python scripts/init_project.py --config my-config.yaml --strict

# Export machine-readable report
python scripts/init_project.py --config my-config.yaml --report-json ./logs/init-report.json
```

## 推荐实战流程（确保 Build Success）

1. 准备环境（JDK 17/21、Maven 3.9+、Python + `pyyaml`）
2. 克隆一份全新 ContiNew 代码副本（不要在生产仓库直接执行）
3. 基于 `assets/config-template.yaml` 填写配置
4. 先执行 `--dry-run --strict --report-json`
5. 再执行正式初始化 `--strict --report-json`
6. 在目标项目中执行编译验证

```bash
# 1) 预演
python scripts/init_project.py --config my-config.yaml --dry-run --strict --report-json ./logs/dry-run.json

# 2) 正式执行
python scripts/init_project.py --config my-config.yaml --strict --report-json ./logs/run.json

# 3) 编译验证（在初始化后的目标项目目录）
mvn clean compile -DskipTests
```

## Claude 使用模板

推荐在 Claude 中显式指定 skill：

```text
/continew-start-skill 请使用 continew-start-skill 初始化 ContiNew 项目。
project_root: D:\test\test_project\continew-admin-dev (此处为ContiNew项目在本地的地址)
brand.new: mytest
package.new: com.mytest.admin
modules.remove: [continew-extension-schedule-server]
先 dry-run，再正式执行，并输出 report-json。
```

说明：
- `/continew-start-skill` 前缀不是强制，但建议保留，触发更稳定
- 需要机器可读结果时，开启 `--report-json`
- 需要将 warning 视为失败时，开启 `--strict`

## 示例配置

```yaml
brand:
  old: continew
  new: mycompany

package:
  old: top.continew.admin
  new: com.mycompany.admin

modules:
  remove:
    - continew-extension-schedule-server
    - continew-plugin-generator

advanced:
  create_backup: true
  backup_location: ../backup
  rollback_on_failure: true
  dry_run: false
  strict: false
  # report_json: ./logs/init-report.json
```

## 项目结构

```text
continew-start-skill/
├── SKILL.md
├── README.md
├── LICENSE
├── scripts/
│   └── init_project.py
├── references/
│   └── replacement-rules.md
└── assets/
    └── config-template.yaml
```

## 重要说明

- 建议始终在新分支执行初始化
- 建议先跑 `--dry-run` 再执行真实改造
- 模块移除后请执行 `mvn clean install` 验证
- 若改了目录结构，请在 IDE 中刷新索引

## 常见问题

| 问题 | 建议 |
|------|------|
| 找不到模块 | 检查模块名是否为短名或正确相对路径 |
| `Child module ... does not exist` | 常见原因是 `pom.xml` 模块名已替换为 `mytest-*`，但目录仍是 `continew-*`。请补全 `directories.rename`（含根模块与 plugin 子模块）后重新执行 |
| Lombok 相关大量报错（`log/getter/构造器` 找不到） | 优先检查 JDK，建议使用 JDK 17 或 JDK 21 后重试 |
| 包路径替换不完整 | 检查 `package.old` 是否与目标仓库一致 |
| 构建失败 | 执行 `mvn clean install` 并检查 `pom.xml` 依赖 |
| 脚本无法运行 | 安装 `pyyaml`：`pip install pyyaml` |

## 文档

- [SKILL.md](SKILL.md) - 技能工作流
- [references/replacement-rules.md](references/replacement-rules.md) - 替换与清理规则
- [assets/config-template.yaml](assets/config-template.yaml) - 配置模板

## 许可证

本项目采用 Apache License 2.0，详见 [LICENSE](LICENSE)。

## 相关链接

- [ContiNew Admin](https://github.com/continew-org/continew-admin)
- [ContiNew Starter](https://github.com/continew-org/continew-starter)
- [ContiNew 文档](https://continew.top)
