<div align="center">

# ContiNew Start Skill

[![Skill Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/itxaiohanglover/continew-start-skill)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7+-brightgreen.svg)](https://www.python.org/downloads/)
[![Claude Skills](https://img.shields.io/badge/Claude-Skills-purple.svg)](https://skills.sh/)

**Automate ContiNew Admin project initialization with custom branding and configuration**

[English](#english) | [中文](#中文)

</div>

---

## English

## Overview

**ContiNew Start Skill** is a Claude Code skill designed to automate the initialization and customization of projects based on the [ContiNew Admin](https://github.com/continew-org/continew-admin) framework. It streamlines the process of branding, package renaming, and project configuration.

### Features

- 🚀 **Quick Initialization**: Set up new projects in minutes, not hours
- 🎨 **Brand Customization**: Replace `continew` branding with your own
- 📦 **Package Refactoring**: Automatically update Java package paths
- 🗂️ **Directory Renaming**: Restructure project directories to match your brand
- ⚙️ **Module Management**: Remove optional components you don't need
- 📝 **Metadata Updates**: Update README, configs, and documentation
- 🌍 **Bilingual Support**: English and Chinese (中文)

### What It Does

| Operation | Description | Example |
|-----------|-------------|---------|
| **Brand Replacement** | Replace brand names in files | `continew` → `mycompany` |
| **Package Path Update** | Update Java package structures | `top.continew.admin` → `com.mycompany.admin` |
| **Directory Rename** | Rename project directories | `continew-admin` → `mycompany-admin` |
| **Content Replace** | Smart text replacement | Preserves `ContiNew` capitalization |
| **Module Removal** | Remove optional modules | `continew-extension-schedule-server` |

## Installation

### Method 1: Using Claude Skills CLI (Recommended)

```bash
npx skills add itxaiohanglover/continew-start-skill
```

### Method 2: Manual Installation

1. Download `continew-start-skill.skill` from [Releases](https://github.com/itxaiohanglover/continew-start-skill/releases)
2. Install using:

```bash
npx skills add path/to/continew-start-skill.skill
```

## Quick Start

### Interactive Mode

Simply ask Claude to initialize your project:

> "Initialize a new ContiNew Admin project called 'MyCompany Admin' with package 'com.mycompany.admin'"

### Configuration File Mode

1. Copy `config-template.yaml` from the `assets/` directory
2. Customize it with your settings:

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

3. Run the initialization script:

```bash
python scripts/init_project.py --config my-config.yaml
```

## Usage Examples

### Example 1: Company Branding

Create a company-branded admin platform:

```yaml
brand:
  old: continew
  new: techcorp

package:
  old: top.continew.admin
  new: com.techcorp.admin
```

### Example 2: Learning Project

Set up a personal learning environment:

```yaml
brand:
  old: continew
  new: learn

package:
  old: top.continew.admin
  new: com.learn.admin

modules:
  remove: []  # Keep all modules
```

### Example 3: SaaS Product

Initialize a SaaS product:

```yaml
brand:
  old: continew
  new: cloudadmin

package:
  old: top.continew.admin
  new: com.saas.cloud

modules:
  remove:
    - continew-extension-schedule-server
    - continew-plugin-generator  # Remove code generator
```

## Project Structure

```
continew-start-skill/
├── SKILL.md                              # Main skill documentation (EN/ZH)
├── README.md                             # This file
├── LICENSE                               # Apache License 2.0
├── scripts/
│   └── init_project.py                   # Python initialization script
├── references/
│   └── replacement-rules.md              # Detailed replacement patterns
└── assets/
    └── config-template.yaml              # Configuration template
```

## Documentation

- **[SKILL.md](SKILL.md)** - Complete skill documentation with workflow details
- **[Replacement Rules](references/replacement-rules.md)** - Comprehensive guide to replacement patterns
- **[Config Template](assets/config-template.yaml)** - Annotated configuration file

## Requirements

- Python 3.7 or higher
- PyYAML library: `pip install pyyaml`

## Important Notes

> **⚠️ Always backup your project before running initialization!**

- **Backup First**: Create a backup of your original project
- **Case Sensitivity**: Replacements preserve capitalization (e.g., `ContiNew` stays `ContiNew`)
- **Module Dependencies**: Verify dependencies before removing modules
- **IDE Settings**: Update IDE project settings after package changes
- **Git History**: Consider initializing new git history for your customized project

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Module not found | Check if the module exists in your project |
| Package path mismatch | Verify the old package name matches your project |
| Import errors after replacement | Run `mvn clean install` to refresh dependencies |

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Links

- [ContiNew Admin](https://github.com/continew-org/continew-admin) - The base framework
- [ContiNew Starter](https://github.com/continew-org/continew-starter) - Starter dependencies
- [ContiNew Documentation](https://continew.top) - Official documentation

## Author

Created by [@itxaiohanglover](https://github.com/itxaiohanglover)

---

## 中文

## 概述

**ContiNew Start Skill** 是一个专为 Claude Code 设计的技能，用于自动化初始化和定制基于 [ContiNew Admin](https://github.com/continew-org/continew-admin) 框架的项目。它简化了品牌化、包重命名和项目配置的流程。

### 功能特性

- 🚀 **快速初始化**：几分钟内完成项目设置，而非数小时
- 🎨 **品牌定制**：将 `continew` 品牌替换为您自己的品牌
- 📦 **包重构**：自动更新 Java 包路径
- 🗂️ **目录重命名**：重组项目目录以匹配您的品牌
- ⚙️ **模块管理**：移除不需要的可选组件
- 📝 **元数据更新**：更新 README、配置文件和文档
- 🌍 **双语支持**：英文和中文

### 功能说明

| 操作 | 描述 | 示例 |
|------|------|------|
| **品牌替换** | 替换文件中的品牌名称 | `continew` → `mycompany` |
| **包路径更新** | 更新 Java 包结构 | `top.continew.admin` → `com.mycompany.admin` |
| **目录重命名** | 重命名项目目录 | `continew-admin` → `mycompany-admin` |
| **内容替换** | 智能文本替换 | 保留 `ContiNew` 首字母大写 |
| **模块移除** | 移除可选模块 | `continew-extension-schedule-server` |

## 安装

### 方法 1：使用 Claude Skills CLI（推荐）

```bash
npx skills add itxaiohanglover/continew-start-skill
```

### 方法 2：手动安装

1. 从 [Releases](https://github.com/itxaiohanglover/continew-start-skill/releases) 下载 `continew-start-skill.skill`
2. 使用以下命令安装：

```bash
npx skills add path/to/continew-start-skill.skill
```

## 快速开始

### 交互模式

直接让 Claude 帮您初始化项目：

> "Initialize a new ContiNew Admin project called 'MyCompany Admin' with package 'com.mycompany.admin'"

### 配置文件模式

1. 从 `assets/` 目录复制 `config-template.yaml`
2. 根据您的需求自定义配置：

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

3. 运行初始化脚本：

```bash
python scripts/init_project.py --config my-config.yaml
```

## 使用示例

### 示例 1：公司品牌化

创建公司品牌的管理局平台：

```yaml
brand:
  old: continew
  new: techcorp

package:
  old: top.continew.admin
  new: com.techcorp.admin
```

### 示例 2：学习项目

设置个人学习环境：

```yaml
brand:
  old: continew
  new: learn

package:
  old: top.continew.admin
  new: com.learn.admin

modules:
  remove: []  # 保留所有模块
```

### 示例 3：SaaS 产品

初始化 SaaS 产品：

```yaml
brand:
  old: continew
  new: cloudadmin

package:
  old: top.continew.admin
  new: com.saas.cloud

modules:
  remove:
    - continew-extension-schedule-server
    - continew-plugin-generator  # 移除代码生成器
```

## 项目结构

```
continew-start-skill/
├── SKILL.md                              # 主技能文档（英文/中文）
├── README.md                             # 本文件
├── LICENSE                               # Apache License 2.0
├── scripts/
│   └── init_project.py                   # Python 初始化脚本
├── references/
│   └── replacement-rules.md              # 详细的替换模式指南
└── assets/
    └── config-template.yaml              # 配置文件模板
```

## 文档

- **[SKILL.md](SKILL.md)** - 完整的技能文档和工作流程详情
- **[替换规则](references/replacement-rules.md)** - 替换模式综合指南
- **[配置模板](assets/config-template.yaml)** - 带注释的配置文件

## 系统要求

- Python 3.7 或更高版本
- PyYAML 库：`pip install pyyaml`

## 重要提示

> **⚠️ 运行初始化前务必备份您的项目！**

- **先备份**：创建原始项目的备份
- **大小写敏感**：替换保留大小写（如 `ContiNew` 保持不变）
- **模块依赖**：移除模块前验证依赖关系
- **IDE 设置**：包更改后更新 IDE 项目设置
- **Git 历史**：考虑为定制的项目初始化新的 git 历史

## 常见问题

### 常见问题解决

| 问题 | 解决方案 |
|------|----------|
| 找不到模块 | 检查模块是否存在于您的项目中 |
| 包路径不匹配 | 验证旧包名是否与您的项目匹配 |
| 替换后导入错误 | 运行 `mvn clean install` 刷新依赖 |

## 贡献

欢迎贡献！请随时提交 Pull Request。

## 许可证

本项目采用 Apache License 2.0 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 相关链接

- [ContiNew Admin](https://github.com/continew-org/continew-admin) - 基础框架
- [ContiNew Starter](https://github.com/continew-org/continew-starter) - Starter 依赖
- [ContiNew 文档](https://continew.top) - 官方文档

## 作者

由 [@itxaiohanglover](https://github.com/itxaiohanglover) 创建

---

<div align="center">

**Made with ❤️ for the ContiNew community**

</div>
