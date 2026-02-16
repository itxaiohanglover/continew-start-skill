---
name: continew-start-skill
description: ContiNew Admin project initialization and customization skill. Use when you need to initialize a new project based on ContiNew Admin framework, including brand renaming (continew -> custom brand), package path replacements (top.continew.admin -> top.custom.admin), directory renames, module removal, and project metadata updates. Supports both interactive mode and configuration file (YAML/JSON) input for batch operations.
---

# ContiNew Start Skill

## Overview

Automates the initialization of projects based on ContiNew Admin framework. Enables rapid project setup with custom branding, package renaming, and module configuration.

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

## Workflow

1. **Gather Requirements** - Ask for brand name, package name, project details
2. **Validate Input** - Check naming conventions, package structure validity
3. **Create Backup** - Recommend backing up original project
4. **Execute Operations** - Perform directory renames, package replacements, content updates
5. **Verify Changes** - Validate all replacements are complete
6. **Update Documentation** - Update README and configuration files

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

## Important Notes

- **Backup First**: Always backup the original project before running initialization
- **Case Sensitivity**: Replacement preserves capitalization (continew vs ContiNew)
- **Module Dependencies**: Some modules have dependencies - verify before removal
- **IDE Configuration**: After package changes, may need to update IDE project settings
- **Git Integration**: Consider initializing git after customization with new project history

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
