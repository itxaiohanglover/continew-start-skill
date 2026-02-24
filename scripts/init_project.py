#!/usr/bin/env python3
"""
Project Initialization Script - Multi-Framework Support

Automates the initialization of ContiNew Admin, RuoYi, and other Java admin framework
projects with custom branding, package renaming, and module configuration.

Supported frameworks: continew, ruoyi

Usage:
    python init_project.py [--config CONFIG_FILE] [--interactive] [--framework FRAMEWORK]

Examples:
    python init_project.py --config my-config.yaml
    python init_project.py --interactive
    python init_project.py --interactive --framework ruoyi
"""

import os
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def _script_dir() -> Path:
    """Get directory containing this script."""
    return Path(__file__).resolve().parent


def _assets_dir() -> Path:
    """Get assets directory (sibling of scripts)."""
    return _script_dir().parent / 'assets'


def load_presets() -> Dict:
    """Load framework presets from YAML."""
    import yaml
    presets_path = _assets_dir() / 'framework-presets.yaml'
    if not presets_path.exists():
        return {}
    with open(presets_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def detect_framework(project_root: Path) -> Optional[str]:
    """Auto-detect framework from project structure."""
    if not project_root.exists():
        return None
    if (project_root / 'ruoyi-admin').exists():
        return 'ruoyi'
    if (project_root / 'continew-admin').exists():
        return 'continew'
    return None


def merge_preset(config: Dict, preset: Dict, brand_new: str) -> Dict:
    """Merge framework preset into config. Uses brand_new to build directory renames."""
    merged = dict(config)

    if 'brand' not in merged:
        merged['brand'] = {}
    merged['brand'].setdefault('old', preset.get('brand', {}).get('old', ''))
    merged['brand']['new'] = merged['brand'].get('new') or brand_new
    merged['brand'].setdefault('cap_old', preset.get('brand', {}).get('cap_old', ''))

    if 'package' not in merged:
        merged['package'] = {}
    merged['package'].setdefault('old', preset.get('package', {}).get('old', ''))

    dirs = preset.get('directories', [])
    if dirs and 'directories' not in merged:
        merged['directories'] = {'rename': []}
    elif 'directories' not in merged:
        merged['directories'] = {'rename': []}

    # Build directory renames from preset if not explicitly provided
    if not merged['directories'].get('rename') and dirs:
        project_root = Path(merged.get('project_root', '.'))
        renames = []
        for d in dirs:
            from_name = d.get('from', '')
            suffix = d.get('suffix', from_name.split('-', 1)[-1] if '-' in from_name else '')
            to_name = f"{brand_new}-{suffix}" if suffix else f"{brand_new}-{from_name}"
            if (project_root / from_name).exists():
                renames.append({'from': from_name, 'to': to_name})
        merged['directories']['rename'] = renames

    return merged


class ProjectInitializer:
    """Handles project initialization and customization for multiple frameworks."""

    def __init__(self, config: Dict):
        self._config = config
        brand_cfg = config.get('brand', {})
        self.brand_old = brand_cfg.get('old', '')
        self.brand_new = brand_cfg.get('new', '')
        self.cap_old = brand_cfg.get('cap_old', '')
        self.cap_new = brand_cfg.get('cap_new', '') or (self.brand_new.capitalize() if self.brand_new else '')
        self.package_old = config.get('package', {}).get('old', '')
        self.package_new = config.get('package', {}).get('new', '')
        self.directories = config.get('directories', {}).get('rename', [])
        self.modules_remove = config.get('modules', {}).get('remove') or []
        self.project_root = Path(config.get('project_root', '.'))
        self.preserve = config.get('preserve', {})
        self.replacements = config.get('replacements', [])
        self.file_renames = config.get('file_renames', [])
        adv = config.get('advanced', {}) or {}
        self.dry_run = adv.get('dry_run', False)

        # Convert package dots to path separators
        self.package_old_path = self.package_old.replace('.', os.sep) if self.package_old else ''
        self.package_new_path = self.package_new.replace('.', os.sep) if self.package_new else ''

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
        adv = self._config.get('advanced', {}) or {}
        if adv.get('create_backup') is False:
            return self.project_root
        loc = adv.get('backup_location', '')
        if loc:
            backup_path = Path(loc)
            if not backup_path.is_absolute():
                backup_path = self.project_root.parent / backup_path
        else:
            backup_path = self.project_root.parent / f"{self.project_root.name}-backup"

        print(f"Creating backup at: {backup_path}")
        if not self.dry_run and not backup_path.exists():
            exclude_dirs = {'.git', 'target', 'node_modules', '__pycache__', '.idea'}
            def _ignore(d, files):
                return [f for f in files if (Path(d) / f).is_dir() and f in exclude_dirs]
            shutil.copytree(self.project_root, backup_path, ignore=_ignore)
            print("Backup complete.")
        elif backup_path.exists():
            print("Backup path already exists, skipping.")

        return backup_path

    def apply_file_renames(self):
        """Apply file renames from config. Executes before directory renames."""
        print("\n=== Applying File Renames ===")
        if not self.file_renames:
            return
        for fr in self.file_renames:
            path = fr.get('path', '')
            new_name = fr.get('new_name', '')
            if not path or not new_name:
                continue
            old_path = self.project_root / path.replace('/', os.sep)
            if not old_path.exists() or not old_path.is_file():
                print(f"Skipping {path}: file not found")
                continue
            new_path = old_path.parent / new_name
            if new_path == old_path:
                continue
            if new_path.exists():
                print(f"Skipping {path}: {new_name} already exists")
                continue
            if self.dry_run:
                print(f"[DRY-RUN] Would rename: {path} -> {new_name}")
            else:
                old_path.rename(new_path)
                print(f"Renamed: {path} -> {new_name}")

    def apply_replacements(self):
        """Apply content replacements from config. Sorted by from length descending."""
        print("\n=== Applying Replacements ===")
        if not self.replacements:
            return
        exts = [
            '.java', '.xml', '.yaml', '.yml', '.ftl', '.sql', '.md', '.html',
            '.vm', '.properties', '.js', '.css', '.javai', '.txt', '.json',
            '.py', '.ts', '.tsx', '.toml', '.ini', '.sh', '.tpl',
        ]
        content_cfg = self._config.get('content', {}) or {}
        extra = content_cfg.get('extra_file_patterns', [])
        if extra:
            for e in extra:
                if e not in exts:
                    exts.append(e)

        repl_list = [(r['from'], r['to']) for r in self.replacements if r.get('from') and r.get('to')]
        if not repl_list:
            return

        for ext in exts:
            glob_pat = '*' + ext if ext.startswith('.') else ext
            for file_path in self.project_root.rglob(glob_pat):
                if self._should_skip_path(file_path):
                    continue
                if file_path.is_file():
                    self._replace_in_file_multi(file_path, repl_list)

        # Handle named files without standard extensions: Dockerfile, Dockerfile.*, Makefile
        for file_path in self.project_root.rglob("*"):
            if not file_path.is_file() or self._should_skip_path(file_path):
                continue
            if file_path.name == "Dockerfile" or file_path.name.startswith("Dockerfile.") or file_path.name == "Makefile":
                self._replace_in_file_multi(file_path, repl_list)

    def rename_package_directories(self):
        """Rename Java package directories (e.g. me/zhengjie -> com/test3)."""
        print("\n=== Renaming Package Directories ===")

        if not self.package_old_path or not self.package_new_path or self.package_old_path == self.package_new_path:
            return

        # Find all src/main/java and src/test/java under project (including nested modules)
        bases = []
        for java_dir in ['src/main/java', 'src/test/java']:
            for base in self.project_root.rglob(java_dir):
                if base.is_dir():
                    bases.append(base)
        for base in bases:
            old_pkg = base / self.package_old_path
            if not old_pkg.exists():
                continue
            new_pkg = base / self.package_new_path
            if new_pkg.exists():
                print(f"Skipping {old_pkg.relative_to(self.project_root)}: target exists")
                continue
            # Check if new_pkg is inside old_pkg (e.g. me.zhengjie -> me.zhengjie.superadmin)
            try:
                new_pkg.resolve().relative_to(old_pkg.resolve())
                is_nested = True
            except ValueError:
                is_nested = False

            if self.dry_run:
                if is_nested:
                    print(f"[DRY-RUN] Would move contents: {old_pkg.relative_to(self.project_root)} -> {new_pkg.relative_to(self.project_root)}")
                else:
                    print(f"[DRY-RUN] Would rename: {old_pkg.relative_to(self.project_root)} -> {new_pkg.relative_to(self.project_root)}")
            else:
                if is_nested:
                    # Create new_pkg and move contents of old_pkg into it (can't rename parent to child)
                    new_pkg.mkdir(parents=True, exist_ok=True)
                    for item in list(old_pkg.iterdir()):
                        if item.name == new_pkg.name:
                            continue
                        dest = new_pkg / item.name
                        if dest.exists():
                            continue
                        shutil.move(str(item), str(dest))
                    print(f"Moved contents: {old_pkg.relative_to(self.project_root)} -> {new_pkg.relative_to(self.project_root)}")
                else:
                    new_pkg.parent.mkdir(parents=True, exist_ok=True)
                    parent_of_old = old_pkg.parent
                    old_pkg.rename(new_pkg)
                    print(f"Renamed: {old_pkg.relative_to(self.project_root)} -> {new_pkg.relative_to(self.project_root)}")
                    candidate = parent_of_old
                    while candidate.exists() and candidate != base:
                        try:
                            candidate.rmdir()
                            candidate = candidate.parent
                        except OSError:
                            break

    def rename_directories(self):
        """Rename directories from framework-* to custom brand."""
        print("\n=== Renaming Directories ===")

        for dir_config in self.directories:
            old_name = dir_config.get('from', '')
            new_name = dir_config.get('to', '')

            if not old_name or not new_name:
                continue

            old_path = self.project_root / old_name
            new_path = self.project_root / new_name

            if old_path.exists() and not new_path.exists():
                if self.dry_run:
                    print(f"[DRY-RUN] Would rename: {old_name} -> {new_name}")
                else:
                    print(f"Renaming: {old_name} -> {new_name}")
                    old_path.rename(new_path)
            elif new_path.exists():
                print(f"Skipping {old_name}: {new_name} already exists")

    def replace_package_paths(self):
        """Replace package paths in Java source files and XML configs."""
        print("\n=== Replacing Package Paths ===")

        if not self.package_old or not self.package_new:
            return

        patterns = [
            '**/*.java', '**/*.xml', '**/*.yaml', '**/*.yml', '**/*.ftl', '**/*.html', '**/*.vm',
            '**/*.properties', '**/*.javai', '**/*.txt', '**/*.py', '**/*.ts', '**/*.tsx',
            '**/*.toml', '**/*.ini', '**/*.sh',
        ]
        content_cfg = getattr(self, '_config', {}).get('content', {}) or {}
        extra = content_cfg.get('extra_file_patterns', [])
        if extra:
            patterns = list(patterns) + list(extra)

        for pattern in patterns:
            for file_path in self.project_root.rglob(pattern):
                if self._should_skip_path(file_path):
                    continue

                self._replace_in_file(file_path, self.package_old, self.package_new)

    def replace_brand_content(self):
        """Replace brand names in file content. Does cap_old->cap_new first, then brand_old->brand_new."""
        print("\n=== Replacing Brand Content ===")

        patterns = [
            '**/*.java', '**/*.xml', '**/*.yaml', '**/*.yml', '**/*.sql', '**/*.ftl', '**/*.md',
            '**/*.html', '**/*.vm', '**/*.properties', '**/*.js', '**/*.css', '**/*.javai',
            '**/*.txt', '**/*.py', '**/*.ts', '**/*.tsx', '**/*.toml', '**/*.ini', '**/*.sh',
        ]
        content_cfg = self._config.get('content', {}) or {}
        extra = content_cfg.get('extra_file_patterns', [])
        if extra:
            patterns = list(patterns) + list(extra)

        replacements = []
        if self.cap_old and self.cap_new:
            replacements.append((self.cap_old, self.cap_new))
        if self.brand_old and self.brand_new:
            replacements.append((self.brand_old, self.brand_new))
        if not replacements:
            return

        for pattern in patterns:
            for file_path in self.project_root.rglob(pattern):
                if self._should_skip_path(file_path):
                    continue

                self._replace_in_file_multi(file_path, replacements)

    def rename_brand_files(self):
        """Rename Java files whose names contain cap_old (e.g. RuoYiConfig.java -> Test2Config.java)."""
        print("\n=== Renaming Brand Files ===")

        if not self.cap_old or not self.cap_new or self.cap_old == self.cap_new:
            return

        for file_path in self.project_root.rglob('**/*.java'):
            if self._should_skip_path(file_path):
                continue
            if self.cap_old not in file_path.name:
                continue
            new_name = file_path.name.replace(self.cap_old, self.cap_new)
            if new_name == file_path.name:
                continue
            new_path = file_path.parent / new_name
            if new_path.exists():
                print(f"Skipping {file_path.name}: {new_name} already exists")
                continue
            if self.dry_run:
                print(f"[DRY-RUN] Would rename: {file_path.relative_to(self.project_root)} -> {new_path.relative_to(self.project_root)}")
            else:
                file_path.rename(new_path)
                print(f"Renamed: {file_path.relative_to(self.project_root)} -> {new_path.relative_to(self.project_root)}")

    def rename_brand_subdirs(self):
        """Rename directories named brand_old to brand_new (e.g. static/ruoyi -> static/test2)."""
        print("\n=== Renaming Brand Subdirectories ===")

        if not self.brand_old or not self.brand_new or self.brand_old == self.brand_new:
            return

        dirs_to_rename = []
        for d in self.project_root.rglob('*'):
            if not d.is_dir() or self._should_skip_path(d):
                continue
            if d.name == self.brand_old:
                dirs_to_rename.append(d)

        for d in sorted(dirs_to_rename, key=lambda p: len(p.parts), reverse=True):
            new_path = d.parent / self.brand_new
            if new_path.exists():
                print(f"Skipping {d.relative_to(self.project_root)}: target exists")
                continue
            if self.dry_run:
                print(f"[DRY-RUN] Would rename: {d.relative_to(self.project_root)} -> {new_path.relative_to(self.project_root)}")
            else:
                d.rename(new_path)
                print(f"Renamed: {d.relative_to(self.project_root)} -> {new_path.relative_to(self.project_root)}")

    def _should_skip_path(self, file_path: Path) -> bool:
        """Check if path should be skipped. Uses path parts to avoid .git matching .github."""
        try:
            rel_path = file_path.relative_to(self.project_root)
        except ValueError:
            rel_path = file_path
        parts = rel_path.parts
        if '.git' in parts:
            return True
        if 'backup' in parts or 'target' in parts or 'node_modules' in parts:
            return True
        if 'venv' in parts or '.venv' in parts or '__pycache__' in parts:
            return True
        if 'ajax' in parts and 'libs' in parts:
            idx_ajax = parts.index('ajax')
            if idx_ajax + 1 < len(parts) and parts[idx_ajax + 1] == 'libs':
                return True
        return False

    def _replace_in_file(self, file_path: Path, old_text: str, new_text: str):
        """Replace text in a file."""
        self._replace_in_file_multi(file_path, [(old_text, new_text)])

    def _replace_in_file_multi(self, file_path: Path, replacements: List[Tuple[str, str]]):
        """Replace multiple patterns in a file. Applies preserve rules if configured."""
        try:
            content = file_path.read_text(encoding='utf-8')
            preserve_patterns = self._get_preserve_patterns()
            preserve_paths = self._get_preserve_paths()

            if preserve_paths and self._path_matches_preserve(file_path, preserve_paths):
                return

            new_content = content
            for old_text, new_text in replacements:
                if preserve_patterns:
                    lines = new_content.splitlines(keepends=True)
                    new_lines = []
                    for line in lines:
                        if any(p in line for p in preserve_patterns):
                            new_lines.append(line)
                        else:
                            new_lines.append(line.replace(old_text, new_text))
                    new_content = ''.join(new_lines)
                else:
                    new_content = new_content.replace(old_text, new_text)

            if new_content != content:
                if self.dry_run:
                    print(f"[DRY-RUN] Would update: {file_path.relative_to(self.project_root)}")
                else:
                    file_path.write_text(new_content, encoding='utf-8')
                    print(f"Updated: {file_path.relative_to(self.project_root)}")

        except (UnicodeDecodeError, PermissionError) as e:
            print(f"Skipping {file_path}: {e}")

    def _get_preserve_patterns(self) -> List[str]:
        """Preserve patterns from config only - no hardcoded defaults."""
        return list(self.preserve.get('patterns') or [])

    def _get_preserve_paths(self) -> List[str]:
        return self.preserve.get('paths') or []

    def _path_matches_preserve(self, file_path: Path, preserve_paths: List[str]) -> bool:
        try:
            rel = file_path.relative_to(self.project_root)
        except ValueError:
            return False
        rel_str = str(rel).replace('\\', '/')
        for pp in preserve_paths:
            pp_norm = pp.replace('\\', '/').strip('/').replace('**/', '')
            if pp_norm and pp_norm in rel_str:
                return True
        return False

    def remove_modules(self):
        """Remove specified modules."""
        print("\n=== Removing Modules ===")

        for module_name in self.modules_remove:
            module_path = self.project_root / module_name

            if module_path.exists():
                if self.dry_run:
                    print(f"[DRY-RUN] Would remove module: {module_name}")
                else:
                    print(f"Removing module: {module_name}")
                    shutil.rmtree(module_path)
            else:
                print(f"Module not found: {module_name}")

    def update_project_metadata(self):
        """Update project metadata files."""
        print("\n=== Updating Project Metadata ===")

        readme_path = self.project_root / 'README.md'
        if readme_path.exists():
            print(f"Review and update: {readme_path}")
            # TODO: Implement README update logic

        changelog_path = self.project_root / 'CHANGELOG.md'
        if changelog_path.exists():
            print(f"Review CHANGELOG.md - consider removing for new project")

    def run(self):
        """Execute the full initialization process."""
        print(f"\n{'='*60}")
        print(f"Project Initializer (Multi-Framework)")
        print(f"{'='*60}")
        print(f"Brand: {self.brand_old} -> {self.brand_new}")
        print(f"Package: {self.package_old} -> {self.package_new}")
        print(f"Project Root: {self.project_root}")
        if self.dry_run:
            print("*** DRY-RUN MODE: No files will be modified ***")
        print(f"{'='*60}\n")

        is_valid, errors = self.validate_config()
        if not is_valid:
            print("Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False

        self.create_backup()

        # Order: 1. file_renames, 2. directories, 3. package dirs, 4. replacements
        self.apply_file_renames()
        self.rename_directories()
        self.rename_package_directories()
        if self.replacements:
            self.apply_replacements()
        else:
            self.replace_package_paths()
            self.replace_brand_content()
            self.rename_brand_files()
        self.rename_brand_subdirs()
        self.remove_modules()
        self.update_project_metadata()

        print("\n" + "="*60)
        print("Initialization complete!")
        print("="*60)
        print("\nNext steps:")
        print("1. Review changes in your IDE")
        print("2. Update project configuration files")
        build = self._config.get('build', {})
        verify_cmd = build.get('verify_command', 'mvn clean install')
        print(f"3. Test build: {verify_cmd}")
        print("4. Initialize git: git init")
        print("5. Commit your new project")

        return True


def load_config(config_file: str) -> Dict:
    """Load configuration from YAML file."""
    import yaml

    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def interactive_mode(framework_hint: Optional[str] = None) -> Dict:
    """Run interactive configuration mode."""
    presets = load_presets()
    project_root = Path('.')

    # Detect or select framework
    framework = framework_hint or detect_framework(project_root)
    if not framework and presets:
        print("Available frameworks: " + ", ".join(presets.keys()))
        fw_input = input("Enter framework (continew/ruoyi) or press Enter to skip: ").strip().lower()
        framework = fw_input if fw_input in presets else None

    preset = presets.get(framework, {}) if framework else {}
    brand_old = preset.get('brand', {}).get('old', 'continew')
    package_old = preset.get('package', {}).get('old', 'top.continew.admin')

    if framework:
        print(f"\nUsing framework preset: {framework}")

    config = {
        'brand': {'old': brand_old},
        'package': {'old': package_old},
        'directories': {'rename': []},
        'modules': {'remove': []},
        'project_root': '.',
    }

    config['brand']['new'] = input(f"Enter new brand name (e.g., mycompany) [{brand_old}]: ").strip().lower() or brand_old
    config['package']['new'] = input(f"Enter new package name (e.g., com.mycompany.admin) [{package_old}]: ").strip() or package_old

    # Optional module removal
    optional = preset.get('optional_modules', [])
    if optional:
        for mod in optional:
            ans = input(f"Remove {mod}? (y/N): ").strip().lower()
            if ans == 'y':
                config['modules']['remove'].append(mod)

    # Merge preset for directory renames
    if preset:
        config = merge_preset(config, preset, config['brand']['new'])

    return config


def main():
    parser = argparse.ArgumentParser(
        description='Initialize ContiNew Admin, RuoYi, or other Java admin framework projects'
    )
    parser.add_argument('--config', '-c', help='Configuration file (YAML)')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--framework', '-f', choices=['continew', 'ruoyi'], help='Framework preset (for interactive or config merge)')
    parser.add_argument('--project-root', '-p', default='.', help='Project root directory')
    parser.add_argument('--dry-run', action='store_true', help='Only print what would be done, do not modify files')

    args = parser.parse_args()

    if args.interactive:
        config = interactive_mode(args.framework)
    elif args.config:
        config = load_config(args.config)
        # Apply framework preset if specified (CLI or config)
        fw = args.framework or config.get('framework')
        if fw:
            presets = load_presets()
            preset = presets.get(fw, {})
            if preset and config.get('brand', {}).get('new'):
                config = merge_preset(config, preset, config['brand']['new'])
    else:
        parser.print_help()
        return 1

    # CLI --project-root overrides config when explicitly set to non-default
    config['project_root'] = args.project_root if args.project_root != '.' else config.get('project_root', '.')
    if args.dry_run:
        config.setdefault('advanced', {})['dry_run'] = True

    initializer = ProjectInitializer(config)
    success = initializer.run()

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
