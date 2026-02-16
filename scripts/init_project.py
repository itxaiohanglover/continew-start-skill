#!/usr/bin/env python3
"""
ContiNew Project Initialization Script

Automates the initialization of ContiNew Admin based projects with custom branding,
package renaming, and module configuration.

Usage:
    python init_project.py [--config CONFIG_FILE] [--interactive]

Examples:
    python init_project.py --config my-config.yaml
    python init_project.py --interactive
"""

import os
import re
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Tuple


class ContiNewInitializer:
    """Handles ContiNew Admin project initialization and customization."""

    def __init__(self, config: Dict):
        self.brand_old = config.get('brand', {}).get('old', 'continew')
        self.brand_new = config.get('brand', {}).get('new', '')
        self.package_old = config.get('package', {}).get('old', 'top.continew.admin')
        self.package_new = config.get('package', {}).get('new', '')
        self.directories = config.get('directories', {}).get('rename', [])
        self.modules_remove = config.get('modules', {}).get('remove', [])
        self.project_root = Path(config.get('project_root', '.'))

        # Convert package dots to path separators
        self.package_old_path = self.package_old.replace('.', os.sep)
        self.package_new_path = self.package_new.replace('.', os.sep)

    def validate_config(self) -> Tuple[bool, List[str]]:
        """Validate configuration before proceeding."""
        errors = []

        if not self.brand_new:
            errors.append("New brand name is required")

        if not self.package_new:
            errors.append("New package name is required")

        if not self.project_root.exists():
            errors.append(f"Project root does not exist: {self.project_root}")

        return len(errors) == 0, errors

    def create_backup(self) -> Path:
        """Create a backup of the project before modifications."""
        backup_name = f"{self.project_root.name}-backup"
        backup_path = self.project_root.parent / backup_name

        print(f"Creating backup at: {backup_path}")
        # TODO: Implement backup logic

        return backup_path

    def rename_directories(self):
        """Rename directories from continew-* to custom brand."""
        print("\n=== Renaming Directories ===")

        for dir_config in self.directories:
            old_name = dir_config.get('from', '')
            new_name = dir_config.get('to', '')

            if not old_name or not new_name:
                continue

            old_path = self.project_root / old_name
            new_path = self.project_root / new_name

            if old_path.exists() and not new_path.exists():
                print(f"Renaming: {old_name} -> {new_name}")
                old_path.rename(new_path)
            elif new_path.exists():
                print(f"Skipping {old_name}: {new_name} already exists")

    def replace_package_paths(self):
        """Replace package paths in Java source files and XML configs."""
        print("\n=== Replacing Package Paths ===")

        # File patterns to process
        patterns = [
            '**/*.java',
            '**/*.xml',
            '**/*.yaml',
            '**/*.yml',
            '**/*.ftl',
        ]

        for pattern in patterns:
            for file_path in self.project_root.rglob(pattern):
                # Skip backup and build directories
                if any(skip in str(file_path) for skip in ['backup', 'target', 'node_modules', '.git']):
                    continue

                self._replace_in_file(file_path, self.package_old, self.package_new)

    def replace_brand_content(self):
        """Replace brand names in file content."""
        print("\n=== Replacing Brand Content ===")

        # File patterns to process
        patterns = [
            '**/*.java',
            '**/*.xml',
            '**/*.yaml',
            '**/*.yml',
            '**/*.sql',
            '**/*.ftl',
            '**/*.md',
        ]

        for pattern in patterns:
            for file_path in self.project_root.rglob(pattern):
                if any(skip in str(file_path) for skip in ['backup', 'target', 'node_modules', '.git']):
                    continue

                self._replace_in_file(file_path, self.brand_old, self.brand_new)

    def _replace_in_file(self, file_path: Path, old_text: str, new_text: str):
        """Replace text in a file."""
        try:
            content = file_path.read_text(encoding='utf-8')
            new_content = content.replace(old_text, new_text)

            if new_content != content:
                file_path.write_text(new_content, encoding='utf-8')
                print(f"Updated: {file_path.relative_to(self.project_root)}")

        except (UnicodeDecodeError, PermissionError) as e:
            print(f"Skipping {file_path}: {e}")

    def remove_modules(self):
        """Remove specified modules."""
        print("\n=== Removing Modules ===")

        for module_name in self.modules_remove:
            module_path = self.project_root / module_name

            if module_path.exists():
                print(f"Removing module: {module_name}")
                shutil.rmtree(module_path)
            else:
                print(f"Module not found: {module_name}")

    def update_project_metadata(self):
        """Update project metadata files."""
        print("\n=== Updating Project Metadata ===")

        # Update README.md
        readme_path = self.project_root / 'README.md'
        if readme_path.exists():
            print(f"Review and update: {readme_path}")
            # TODO: Implement README update logic

        # Remove or update CHANGELOG.md
        changelog_path = self.project_root / 'CHANGELOG.md'
        if changelog_path.exists():
            print(f"Review CHANGELOG.md - consider removing for new project")

    def run(self):
        """Execute the full initialization process."""
        print(f"\n{'='*60}")
        print(f"ContiNew Project Initializer")
        print(f"{'='*60}")
        print(f"Brand: {self.brand_old} -> {self.brand_new}")
        print(f"Package: {self.package_old} -> {self.package_new}")
        print(f"Project Root: {self.project_root}")
        print(f"{'='*60}\n")

        # Validate
        is_valid, errors = self.validate_config()
        if not is_valid:
            print("Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False

        # Create backup
        self.create_backup()

        # Execute operations
        self.rename_directories()
        self.replace_package_paths()
        self.replace_brand_content()
        self.remove_modules()
        self.update_project_metadata()

        print("\n" + "="*60)
        print("Initialization complete!")
        print("="*60)
        print("\nNext steps:")
        print("1. Review changes in your IDE")
        print("2. Update project configuration files")
        print("3. Test build: mvn clean install (backend)")
        print("4. Initialize git: git init")
        print("5. Commit your new project")

        return True


def load_config(config_file: str) -> Dict:
    """Load configuration from YAML file."""
    import yaml

    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def interactive_mode() -> Dict:
    """Run interactive configuration mode."""
    print("\n=== ContiNew Project Initialization - Interactive Mode ===\n")

    config = {
        'brand': {
            'old': 'continew'
        },
        'package': {
            'old': 'top.continew.admin'
        },
        'directories': {
            'rename': []
        },
        'modules': {
            'remove': []
        },
        'project_root': '.'
    }

    # Get user input
    config['brand']['new'] = input("Enter new brand name (e.g., mycompany): ").strip().lower()
    config['package']['new'] = input("Enter new package name (e.g., com.mycompany.admin): ").strip()

    # Ask about modules
    remove_schedule = input("Remove schedule-server module? (y/N): ").strip().lower()
    if remove_schedule == 'y':
        config['modules']['remove'].append('continew-extension-schedule-server')

    # Generate directory renames
    brand_old = config['brand']['old']
    brand_new = config['brand']['new']

    # Common directory renames
    directories = [
        ('continew-admin', f'{brand_new}-admin'),
        ('continew-server', f'{brand_new}-server'),
        ('continew-system', f'{brand_new}-system'),
        ('continew-common', f'{brand_new}-common'),
        ('continew-plugin', f'{brand_new}-plugin'),
        ('continew-extension', f'{brand_new}-extension'),
    ]

    for old_dir, new_dir in directories:
        if (Path('.') / old_dir).exists():
            config['directories']['rename'].append({'from': old_dir, 'to': new_dir})

    return config


def main():
    parser = argparse.ArgumentParser(description='Initialize ContiNew Admin based project')
    parser.add_argument('--config', '-c', help='Configuration file (YAML)')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')

    args = parser.parse_args()

    if args.interactive:
        config = interactive_mode()
    elif args.config:
        config = load_config(args.config)
    else:
        parser.print_help()
        return 1

    initializer = ContiNewInitializer(config)
    success = initializer.run()

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
