# ContiNew Admin Replacement Rules

This document defines practical replacement and cleanup rules for customizing ContiNew Admin projects.

## 1. Brand Replacement

### 1.1 Content rules

| Pattern | Action | Notes |
|---------|--------|-------|
| `continew` | Replace with `{new_brand}` | Replace by token boundary (avoid accidental substring replacement) |
| `ContiNew` | Keep by default | Preserve brand capitalization unless explicitly required |
| `CONTINEW` | Optional custom replacement | Apply only when constant names must be aligned |

### 1.2 Directory rename rules

**Root modules**

```text
continew-admin      -> {new-brand}-admin
continew-server     -> {new-brand}-server
continew-system     -> {new-brand}-system
continew-common     -> {new-brand}-common
continew-plugin     -> {new-brand}-plugin
continew-extension  -> {new-brand}-extension
```

**Submodules (optional)**

```text
continew-plugin/continew-plugin-open      -> {new-brand}-plugin/{new-brand}-plugin-open
continew-plugin/continew-plugin-tenant    -> {new-brand}-plugin/{new-brand}-plugin-tenant
continew-plugin/continew-plugin-schedule  -> {new-brand}-plugin/{new-brand}-plugin-schedule
continew-plugin/continew-plugin-generator -> {new-brand}-plugin/{new-brand}-plugin-generator
continew-extension/continew-extension-schedule-server -> {new-brand}-extension/{new-brand}-extension-schedule-server
```

## 2. Package Replacement

### 2.1 Replace scope

- Replace only `top.continew.admin` and `top/continew/admin`
- Common files: `*.java`, `*.xml`, `*.yml`, `*.yaml`, `*.ftl`, `*.properties`

### 2.2 Protected literals (must NOT be replaced)

Do not replace these values:

- `top.continew.starter`
- `top/continew/starter`
- `continew-starter`

Reason: these are external Starter dependencies, not project namespace.

## 3. Module Removal Rules

### 3.1 Supported module names

Short name or relative path are both acceptable:

- `continew-extension-schedule-server`
- `continew-extension/continew-extension-schedule-server`
- `continew-plugin-schedule`
- `continew-plugin-generator`

### 3.2 Mandatory sync after deletion

After removing a module directory, also remove related entries from `pom.xml`:

1. `<module>...</module>` in aggregator POMs
2. `<dependency>...<artifactId>removed-module</artifactId>...</dependency>` in dependent modules

If you only delete files without updating POMs, Maven build will fail.

## 4. Metadata Update Rules

Minimum recommended updates:

- `README.md` project title/description
- Optional: `CHANGELOG.md` strategy (keep or reset)
- Optional: license holder info

## 5. Safety Strategy

### 5.1 Before execution

- Run in a feature branch
- Enable backup
- Prefer `--dry-run` first

### 5.2 During execution

- Exclude heavy/generated paths (`.git`, `target`, `node_modules`, etc.)
- Record updated files and replacement counts

### 5.3 On failure

- Roll back from backup if enabled

## 6. Post-Run Checklist

1. Verify no unexpected `top.continew.admin` remains
2. Verify Starter namespace is intact (`top.continew.starter`)
3. Run backend build:

```bash
mvn clean install
```

4. Refresh IDE indexing
5. Run smoke tests for startup and key APIs

## 7. Common Pitfalls

- Replacing `top.continew.starter` by mistake
- Deleting module directories without cleaning POM references
- Renaming parent directories before children (path conflicts)
- Running directly without dry-run and backup
