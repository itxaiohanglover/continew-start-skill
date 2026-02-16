# ContiNew Admin Replacement Rules

This document details all replacement patterns and rules for customizing ContiNew Admin projects.

## Brand Naming Replacement

### Content Replacement Rules

| Pattern | Replacement | Scope | Notes |
|---------|-------------|-------|-------|
| `continew` | `{new_brand}` | Java, XML, YAML, SQL, FTL | Only lowercase, preserves `ContiNew` |
| `ContiNew` | Keep unchanged | All files | Brand name with capitalization |
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
continew-plugin/continew-plugin-tenant -> {new-brand}-plugin/{new-brand}-plugin-tenant
continew-plugin/continew-plugin-schedule -> {new-brand}-plugin/{new-brand}-plugin-schedule
continew-plugin/continew-plugin-generator -> {new-brand}-plugin/{new-brand}-plugin-generator
```

**Extension Submodules:**
```
continew-extension/continew-extension-schedule-server -> {new-brand}-extension/{new-brand}-extension-schedule-server
```

**Docker:**
```
docker/continew-admin -> docker/{new-brand}-admin
```

## Package Path Replacement

### Java Package Structure

**Old Structure:**
```
top/
└── continew/
    └── admin/
        ├── common/
        ├── system/
        ├── plugin/
        └── server/
```

**New Structure:**
```
{base_package}/
└── {brand}/
    └── admin/
        ├── common/
        ├── system/
        ├── plugin/
        └── server/
```

### Package Import Statements

**Before:**
```java
import top.continew.admin.common.model.entity.BaseDO;
import top.continew.admin.system.api.UserApi;
```

**After:**
```java
import {new_package}.common.model.entity.BaseDO;
import {new_package}.system.api.UserApi;
```

### MyBatis Mapper XML

**Before:**
```xml
<mapper namespace="top.continew.admin.system.mapper.UserMapper">
```

**After:**
```xml
<mapper namespace="{new_package}.system.mapper.UserMapper">
```

### Maven Configuration (pom.xml)

**Dependencies:**
```xml
<!-- Before -->
<groupId>top.continew</groupId>
<artifactId>continew-admin</artifactId>

<!-- After -->
<groupId>{new_group_id}</groupId>
<artifactId>{new_brand}-admin</artifactId>
```

## File Content Replacements

### Configuration Files

**application.yml:**
```yaml
# Before
name: continew-admin

# After
name: {new_brand}-admin
```

### API Documentation

**Controller Tags:**
```java
// Before
@Tag(name = "ContiNew Admin API")

// After
@Tag(name = "{Project Name} API")
```

### README.md Updates

Key sections to update:
- Project title and description
- Badge links and references
- Author/maintainer information
- Documentation links
- License holder

## Module Removal Guide

### Safe to Remove

**continew-extension-schedule-server**
- Purpose: Standalone task scheduling server
- When to remove: Company provides centralized scheduling infrastructure
- Dependencies: Low - highly decoupled from main application

### Plugin Modules

**continew-plugin-schedule**
- Purpose: Task scheduling integration
- When to remove: Not using distributed task scheduling
- Dependencies: Moderate - check for scheduled tasks in code

**continew-plugin-generator**
- Purpose: Code generation
- When to remove: Code generation not needed
- Dependencies: Low - isolated functionality

### Keep for Full Functionality

**continew-plugin-open** - API/Open platform features
**continew-plugin-tenant** - Multi-tenancy support
**continew-common** - Core shared functionality
**continew-system** - System management features

## Special Cases

### Starter Dependencies

ContiNew Starter dependencies typically should NOT be renamed:
```xml
<!-- Keep these as-is -->
<dependency>
    <groupId>top.continew.starter</groupId>
    <artifactId>continew-starter-web</artifactId>
</dependency>
```

These are external dependencies published to Maven Central.

### Third-Party Integrations

When replacing brand names in third-party integration code:
- Check for API key/secret references
- Update OAuth callback URLs
- Verify webhook endpoints

## Post-Renaming Tasks

1. **IDE Configuration**
   - Update project structure in IntelliJ IDEA
   - Refresh Maven dependencies
   - Re-index code base

2. **Build Verification**
   ```bash
   mvn clean install
   ```

3. **Git Initialization**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Customized from ContiNew Admin"
   ```

4. **Documentation Updates**
   - Update all README references
   - Update API documentation links
   - Update deployment guides

## Common Pitfalls

### Case Sensitivity Issues

**Problem:** Replacing all occurrences including capitalized "ContiNew"
**Solution:** Only replace lowercase "continew" in content

**Problem:** Breaking constant names like CONTINEW_ADMIN
**Solution:** Preserve constants or update consistently

### Module Dependencies

**Problem:** Removing modules with undeclared dependencies
**Solution:** Always check for import statements before removal

### Build Failures

**Problem:** Package path mismatches after replacement
**Solution:** Verify all imports, especially in test files
