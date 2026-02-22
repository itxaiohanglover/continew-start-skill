---
name: continew-start-skill
description: ContiNew Admin 项目初始化和定制技能。用于基于 ContiNew Admin 快速二次初始化：品牌重命名、包路径替换、目录重命名、可选模块移除（含 Maven pom 联动清理）、项目元数据更新，并支持 dry-run、备份与失败回滚。
---

# ContiNew Start Skill

## 概述

自动化基于 ContiNew Admin 框架的项目初始化，目标是在保持可控风险的前提下，完成品牌化与工程改造。

## 快速开始

### 交互模式

让 Claude 帮你初始化 ContiNew 项目：

> "初始化一个新的 ContiNew Admin 项目，名称为 'MyCompany Admin'，包名为 'com.mycompany.admin'"

### 配置文件模式

提供包含替换规则的 YAML 配置文件：

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

advanced:
  create_backup: true
  backup_location: ../backup
  rollback_on_failure: true
  dry_run: false
```

运行：

```bash
python scripts/init_project.py --config my-config.yaml
```

仅预览不落盘：

```bash
python scripts/init_project.py --config my-config.yaml --dry-run
```

## 核心操作

### 1. 目录重命名

将项目目录从 `continew-*` 重命名为自定义品牌名。

### 2. 包路径替换

更新代码库中的 `top.continew.admin` 与 `top/continew/admin`。

### 3. 内容替换

替换品牌相关字符串：仅按词边界替换小写 `continew`，保留 `ContiNew`。

### 4. 模块移除（含依赖清理）

删除指定模块目录，并自动在各级 `pom.xml` 中清理对应 `<module>` 与 `<dependency>` 条目。

### 5. 项目元数据更新

按配置更新 README 等元信息。

## 安全机制

- 支持备份目录（建议放在项目外）
- 支持 `dry-run` 预演
- 失败后可自动回滚（依赖备份）
- 默认排除 `.git/target/node_modules` 等目录
- 保护 `top.continew.starter` 与 `continew-starter`，避免误改外部 Starter 依赖

## 工作流程

1. 收集需求（品牌名、包名、模块策略）
2. 校验输入（命名与路径）
3. 创建备份
4. 执行操作（删模块、改目录、替换、元数据）
5. 后置校验（残留包名扫描）
6. 人工复核并编译验证

## 资源

### scripts/init_project.py

主执行脚本，负责：
- 路径解析与配置加载
- 目录重命名
- 包路径与品牌替换
- 模块删除与 `pom.xml` 联动清理
- 备份、回滚、dry-run、报告输出

### references/replacement-rules.md

替换模式与注意事项（包括 Starter 保护、模块清理规则）。

### assets/config-template.yaml

配置模板（含高级选项和示例）。

## 重要提示

- 初始化前建议在 Git 分支执行
- 先 `--dry-run`，确认变更范围
- 模块移除后务必执行 `mvn clean install`
- 如果改动了目录结构，记得刷新 IDE 索引

## 语言

本技能使用中文编写。
