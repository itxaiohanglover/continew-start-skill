---
name: continew-start-skill
description: ContiNew Admin project initialization and customization skill. Use when you need to initialize a new project based on ContiNew Admin framework, including brand renaming (continew -> custom brand), package path replacements (top.continew.admin -> top.custom.admin), directory renames, module removal, and project metadata updates. Supports both interactive mode and configuration file (YAML/JSON) input for batch operations.
---

# ContiNew Start Skill

## Overview

Automates the initialization of projects based on ContiNew Admin framework. Enables rapid project setup with custom branding, package renaming, and module configuration.

## 概述

自动化基于 ContiNew Admin 框架的项目初始化。支持快速自定义品牌、包名重命名和模块配置。

---

## Quick Start

### Interactive Mode

Ask Claude to initialize a ContiNew project with your custom branding:

> "Initialize a new ContiNew Admin project called 'MyCompany Admin' with package 'com.mycompany.admin'"

### Configuration File Mode

Provide a YAML configuration file with all replacement rules:

```yaml
brand:
  old: continew
  new: mycompany

package:
  old: top.continew.admin
  new: com.mycompany.admin

directories:
  rename:
    - from: continew-admin
      to: mycompany-admin
    - from: continew-server
      to: mycompany-server

modules:
  remove:
    - continew-extension-schedule-server
```

## 快速开始

### 交互模式

让 Claude 帮你初始化 ContiNew 项目：

> "Initialize a new ContiNew Admin project called 'MyCompany Admin' with package 'com.mycompany.admin'"

### 配置文件模式

提供包含所有替换规则的 YAML 配置文件：

```yaml
brand:
  old: continew
  new: mycompany

package:
  old: top.continew.admin
  new: com.mycompany.admin

directories:
  rename:
    - from: continew-admin
      to: mycompany-admin
    - from: continew-server
      to: mycompany-server

modules:
  remove:
    - continew-extension-schedule-server
```

---

## Core Operations

### 1. Directory Renaming

Renames project directories from continew-* to your custom brand name.

**Scope:**
- Root modules: continew-server, continew-system, continew-common, continew-plugin, continew-extension
- Plugin submodules: continew-plugin-*, continew-extension-*
- Docker directories

### 2. Package Path Replacement

Updates Java package paths throughout the codebase.

**Scope:**
- All Java source files (*.java)
- MyBatis mapper XML files
- Configuration files (application.yml, pom.xml)

**Pattern:**
```
top/continew/admin -> top/yourbrand/admin
top.continew.admin -> top.yourbrand.admin
```

### 3. Content Replacement

Replaces brand-related strings in source files.

**Scope:**
- Java, XML, YAML, SQL, FTL files
- Only lowercase 'continew' is replaced (preserves 'ContiNew' capitalization)
- Configurable replacement rules

### 4. Project Metadata Updates

Updates project metadata files:

**Files:**
- README.md
- package.json (frontend)
- pom.xml (backend Maven modules)
- package-lock.json
- CHANGELOG.md (remove or update)

### 5. Module Removal

Removes optional modules that are highly decoupled.

**Removable Modules:**
- `continew-extension-schedule-server` - Task scheduling server (if company provides centralized infrastructure)
- Plugin modules based on business needs

## 核心操作

### 1. 目录重命名

将项目目录从 continew-* 重命名为你的自定义品牌名。

**范围：**
- 根模块：continew-server、continew-system、continew-common、continew-plugin、continew-extension
- 插件子模块：continew-plugin-*、continew-extension-*
- Docker 目录

### 2. 包路径替换

更新整个代码库中的 Java 包路径。

**范围：**
- 所有 Java 源文件 (*.java)
- MyBatis Mapper XML 文件
- 配置文件 (application.yml、pom.xml)

**模式：**
```
top/continew/admin -> top/yourbrand/admin
top.continew.admin -> top.yourbrand.admin
```

### 3. 内容替换

替换源文件中的品牌相关字符串。

**范围：**
- Java、XML、YAML、SQL、FTL 文件
- 仅替换小写 'continew'（保留 'ContiNew' 首字母大写）
- 可配置替换规则

### 4. 项目元数据更新

更新项目元数据文件：

**文件：**
- README.md
- package.json（前端）
- pom.xml（后端 Maven 模块）
- package-lock.json
- CHANGELOG.md（删除或更新）

### 5. 模块移除

移除高内聚低耦合的可选模块。

**可移除模块：**
- `continew-extension-schedule-server` - 任务调度服务器（如果公司提供集中式基础设施）
- 根据业务需求的插件模块

---

## Workflow

1. **Gather Requirements** - Ask for brand name, package name, project details
2. **Validate Input** - Check naming conventions, package structure validity
3. **Create Backup** - Recommend backing up original project
4. **Execute Operations** - Perform directory renames, package replacements, content updates
5. **Verify Changes** - Validate all replacements are complete
6. **Update Documentation** - Update README and configuration files

## 工作流程

1. **收集需求** - 询问品牌名、包名、项目详情
2. **验证输入** - 检查命名规范、包结构有效性
3. **创建备份** - 建议备份原始项目
4. **执行操作** - 执行目录重命名、包替换、内容更新
5. **验证更改** - 验证所有替换是否完成
6. **更新文档** - 更新 README 和配置文件

---

## Resources

### scripts/init_project.py

Main Python script that executes the initialization process. Handles:
- Directory traversal and renaming
- File content search and replace
- Package path updates
- Module removal

### references/replacement-rules.md

Detailed documentation of replacement patterns and rules for ContiNew Admin project structure.

### assets/config-template.yaml

Template configuration file for batch operations.

## 资源

### scripts/init_project.py

执行初始化过程的 Python 主脚本。处理：
- 目录遍历和重命名
- 文件内容搜索和替换
- 包路径更新
- 模块移除

### references/replacement-rules.md

ContiNew Admin 项目结构的替换模式和规则详细文档。

### assets/config-template.yaml

批量操作的配置文件模板。

---

## Important Notes

- **Backup First**: Always backup the original project before running initialization
- **Case Sensitivity**: Replacement preserves capitalization (continew vs ContiNew)
- **Module Dependencies**: Some modules have dependencies - verify before removal
- **IDE Configuration**: After package changes, may need to update IDE project settings
- **Git Integration**: Consider initializing git after customization with new project history

## 重要提示

- **先备份**：运行初始化前始终备份原始项目
- **大小写敏感**：替换保留大小写（continew vs ContiNew）
- **模块依赖**：某些模块有依赖关系 - 移除前请验证
- **IDE 配置**：包更改后，可能需要更新 IDE 项目设置
- **Git 集成**：自定义后考虑使用新项目历史初始化 git

---

## Common Use Cases

### Use Case 1: Company Branding

Transform ContiNew Admin to company-branded solution:
- Brand: TechCorp
- Package: com.techcorp.admin
- Remove: schedule-server (using centralized infrastructure)

### Use Case 2: Learning Project

Create a learning environment:
- Brand: MyAdmin
- Package: com.learn.admin
- Keep all modules for exploration

### Use Case 3: SaaS Product

Initialize SaaS product based on ContiNew:
- Brand: CloudAdmin
- Package: com.saas.cloud
- Customize: Remove internal-only features

## 常见用例

### 用例 1：公司品牌化

将 ContiNew Admin 转换为公司品牌解决方案：
- 品牌：TechCorp
- 包：com.techcorp.admin
- 移除：schedule-server（使用集中式基础设施）

### 用例 2：学习项目

创建学习环境：
- 品牌：MyAdmin
- 包：com.learn.admin
- 保留所有模块用于探索

### 用例 3：SaaS 产品

基于 ContiNew 初始化 SaaS 产品：
- 品牌：CloudAdmin
- 包：com.saas.cloud
- 自定义：移除仅内部使用的功能

---

## Language / 语言

This skill supports both English and Chinese (中文). Default language is English.

本技能支持英文和中文。默认语言为英文。
