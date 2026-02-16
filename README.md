# ContiNew Start Skill

A Claude Code skill for automating the initialization of ContiNew Admin based projects with custom branding, package renaming, and module configuration.

## Overview

This skill helps you quickly customize and initialize projects based on the [ContiNew Admin](https://github.com/continew-org/continew-admin) framework. It automates:

- **Brand Renaming**: Replace `continew` with your custom brand name
- **Package Path Replacement**: Update Java package paths throughout the codebase
- **Directory Renaming**: Rename project directories to match your brand
- **Content Replacement**: Smart text replacement preserving capitalization
- **Module Removal**: Remove optional decoupled modules
- **Metadata Updates**: Update README, configuration files, and project metadata

## Installation

1. Download `continew-start-skill.skill`
2. Install using Claude Skills CLI:

```bash
npx skills add path/to/continew-start-skill.skill
```

## Usage

### Interactive Mode

Simply ask Claude to initialize a ContiNew project:

> "Initialize a new ContiNew Admin project called 'MyCompany Admin' with package 'com.mycompany.admin'"

### Configuration File Mode

Create a configuration file based on `assets/config-template.yaml` and run:

```bash
python scripts/init_project.py --config my-config.yaml
```

## Configuration Template

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

## Features

- **Smart Case Preservation**: Only replaces lowercase `continew`, preserves `ContiNew`
- **Backup Creation**: Automatically creates backup before modifications
- **Dry Run Mode**: Preview changes without applying them
- **Modular Design**: Supports removing optional components
- **Cross-Platform**: Works on Windows, Linux, and macOS

## Documentation

- `SKILL.md` - Main skill documentation
- `references/replacement-rules.md` - Detailed replacement patterns and rules
- `assets/config-template.yaml` - Configuration file template

## Requirements

- Python 3.7+
- PyYAML (`pip install pyyaml`)

## License

This skill is provided as-is for customizing ContiNew Admin projects. Please refer to the [ContiNew Admin License](https://github.com/continew-org/continew-admin/blob/dev/LICENSE) for the framework itself.

## Links

- [ContiNew Admin](https://github.com/continew-org/continew-admin)
- [ContiNew Starter](https://github.com/continew-org/continew-starter)
- [ContiNew Documentation](https://continew.top)

## Author

Created by [itxaiohanglover](https://github.com/itxaiohanglover)
