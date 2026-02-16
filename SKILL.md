---
name: continew-start-skill
description: ContiNew Admin 项目初始化和定制技能。当你需要基于 ContiNew Admin 框架初始化新项目时使用，包括品牌重命名（continew -> 自定义品牌）、包路径替换（top.continew.admin -> top.custom.admin）、目录重命名、模块移除和项目元数据更新。支持交互模式和配置文件（YAML/JSON）批量操作。
---

# ContiNew Start Skill

## 概述

自动化基于 ContiNew Admin 框架的项目初始化。支持快速自定义品牌、包名重命名和模块配置。

## 快速开始

### 交互模式

让 Claude 帮你初始化 ContiNew 项目：

> "初始化一个新的 ContiNew Admin 项目，名称为 'MyCompany Admin'，包名为 'com.mycompany.admin'"

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

## 工作流程

1. **收集需求** - 询问品牌名、包名、项目详情
2. **验证输入** - 检查命名规范、包结构有效性
3. **创建备份** - 建议备份原始项目
4. **执行操作** - 执行目录重命名、包替换、内容更新
5. **验证更改** - 验证所有替换是否完成
6. **更新文档** - 更新 README 和配置文件

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

## 重要提示

- **先备份**：运行初始化前始终备份原始项目
- **大小写敏感**：替换保留大小写（continew vs ContiNew）
- **模块依赖**：某些模块有依赖关系 - 移除前请验证
- **IDE 配置**：包更改后，可能需要更新 IDE 项目设置
- **Git 集成**：自定义后考虑使用新项目历史初始化 git

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

## 语言

本技能使用中文编写。
