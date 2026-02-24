# Project Replacement Rules - Multi-Framework

This document details replacement patterns and rules for customizing ContiNew Admin, RuoYi, and other Java admin framework projects.

---

## ContiNew Admin

### Brand Naming Replacement

| Pattern | Replacement | Scope | Notes |
|---------|-------------|-------|-------|
| `continew` | `{new_brand}` | Java, XML, YAML, SQL, FTL | Only lowercase, preserves `ContiNew` |
| `ContiNew` | `{cap_new}` | All files | 通过 cap_old/cap_new 配置替换 |
| `CONTINEW` | `{NEW_BRAND_UPPER}` | Constants | If needed for consistency |

### Directory Renaming Patterns

**Root Modules:**
```
continew-admin -> {new-brand}-admin
continew-server -> {new-brand}-server
continew-system -> {new-brand}-system
continew-common -> {new-brand}-common
continew-plugin -> {new-brand}-plugin
continew-extension -> {new-brand}-extension
```

**Plugin Submodules:**
```
continew-plugin/continew-plugin-open -> {new-brand}-plugin/{new-brand}-plugin-open
continew-extension/continew-extension-schedule-server -> {new-brand}-extension/{new-brand}-extension-schedule-server
```

### Package Path Replacement

**Old:** `top.continew.admin` → **New:** `{new_package}`

**Scope:** Java、XML、YAML、HTML、VM、properties（排除 ajax/libs）

### Module Removal Guide

- **continew-extension-schedule-server** - Safe to remove if using centralized scheduling
- **continew-plugin-generator** - Safe to remove if code generation not needed

---

## RuoYi

### Brand Naming Replacement

| Pattern | Replacement | Scope | Notes |
|---------|-------------|-------|-------|
| `ruoyi` | `{new_brand}` | Java, XML, YAML, SQL, HTML | Lowercase brand name |
| `RuoYi` | `{NewBrand}` | Display names | Capitalized form |

### Directory Renaming Patterns

**Root Modules:**
```
ruoyi-admin -> {new-brand}-admin
ruoyi-framework -> {new-brand}-framework
ruoyi-system -> {new-brand}-system
ruoyi-quartz -> {new-brand}-quartz
ruoyi-generator -> {new-brand}-generator
ruoyi-common -> {new-brand}-common
```

### Package Path Replacement

**Old:** `com.ruoyi` → **New:** `com.{new_brand}` (e.g., `com.mycompany`)

**Scope:** Java、XML、YAML、HTML、VM、properties、JS、CSS（排除 ajax/libs）

- Java source: `com/ruoyi/` directory structure, import statements
- MyBatis Mapper XML: `namespace="com.ruoyi.system.mapper.XxxMapper"`
- application.yml: `typeAliasesPackage: com.ruoyi.**.domain`
- generator.yml: `packageName: com.ruoyi.system`

### RuoYi-Specific Configuration

**application.yml** - Top-level key replacement:
```yaml
# Before
ruoyi:
  name: RuoYi
  profile: D:/ruoyi/uploadPath

# After
mycompany:
  name: MyCompany
  profile: D:/mycompany/uploadPath
```

**generator.yml** - Package name:
```yaml
# Before
packageName: com.ruoyi.system

# After
packageName: com.mycompany.system
```

### Module Removal Guide

- **ruoyi-quartz** - Safe to remove if not using scheduled tasks
- **ruoyi-generator** - Safe to remove if code generation not needed

### Keep for Full Functionality

- **ruoyi-common** - Core shared functionality
- **ruoyi-framework** - Web/Security framework
- **ruoyi-system** - System management
- **ruoyi-admin** - Web entry module

---

## Common Rules (All Frameworks)

### Post-Renaming Tasks

1. **IDE Configuration** - Refresh Maven, re-index
2. **Build Verification** - `mvn clean install`
3. **Git Initialization** - `git init` for new project history
4. **Documentation** - Update README, API docs

### Common Pitfalls

- **Case Sensitivity** - Replace lowercase brand only; preserve capitalized forms
- **Module Dependencies** - Check imports before removing modules
- **Build Failures** - Verify all package paths, especially in test files

### Exclude Patterns

Always exclude from replacement: `node_modules`, `target`, `.git`, `*.iml`, `.idea`, `*.class`, `ajax/libs`

### Preserve Configuration

- **preserve.patterns**：包含这些字符串的行不替换（如 `top.continew.starter`、`continew-starter`）
- **preserve.paths**：这些路径下的文件完全跳过（如 `**/ajax/libs/**`）

### Cap Old / Cap New

- **cap_old** / **cap_new**：用于替换类名、文件名中的 PascalCase 品牌（如 RuoYi→Test2、ContiNew→Mycompany）
- 同时触发 `rename_brand_files`（重命名含 cap_old 的 .java 文件）和 `rename_brand_subdirs`（如 static/ruoyi→static/test2）
