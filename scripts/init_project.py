#!/usr/bin/env python3
"""
ContiNew Project Initialization Script

Automates ContiNew Admin project initialization with safer replacement and
module-aware cleanup.
"""

import argparse
import fnmatch
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

try:
    import yaml
except ImportError as exc:
    print("Missing dependency: pyyaml. Install with: pip install pyyaml")
    raise exc


DEFAULT_TEXT_PATTERNS = ("**/*.java", "**/*.xml", "**/*.yaml", "**/*.yml", "**/*.sql", "**/*.ftl", "**/*.md")
PACKAGE_PATTERNS = ("**/*.java", "**/*.xml", "**/*.yaml", "**/*.yml", "**/*.ftl", "**/*.properties")
DEFAULT_EXCLUDES = (".git/**", "target/**", "node_modules/**", ".idea/**", "*.iml", "*.class")
PROTECTED_LITERALS = ("top.continew.starter", "top/continew/starter", "continew-starter")
KNOWN_MODULE_PATHS = {
    "continew-extension-schedule-server": "continew-extension/continew-extension-schedule-server",
    "continew-plugin-schedule": "continew-plugin/continew-plugin-schedule",
    "continew-plugin-generator": "continew-plugin/continew-plugin-generator",
    "continew-plugin-open": "continew-plugin/continew-plugin-open",
    "continew-plugin-tenant": "continew-plugin/continew-plugin-tenant",
}


@dataclass
class ExecutionReport:
    files_scanned: int = 0
    files_updated: int = 0
    replacements: int = 0
    dirs_renamed: List[str] = field(default_factory=list)
    dirs_removed: List[str] = field(default_factory=list)
    pom_updated: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    missing_modules: List[str] = field(default_factory=list)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


class ContiNewInitializer:
    """Handles ContiNew Admin project initialization and customization."""

    def __init__(self, config: Dict, config_file: Optional[Path] = None, cli_dry_run: bool = False):
        config = config or {}
        self.config_file = config_file.resolve() if config_file else None
        self.config_base_dir = self.config_file.parent if self.config_file else Path.cwd()

        self.brand_old = config.get("brand", {}).get("old", "continew").strip()
        self.brand_new = config.get("brand", {}).get("new", "").strip()
        self.package_old = config.get("package", {}).get("old", "top.continew.admin").strip()
        self.package_new = config.get("package", {}).get("new", "").strip()
        self.directories = config.get("directories", {}).get("rename", []) or []
        self.modules_remove = config.get("modules", {}).get("remove", []) or []

        raw_project_root = config.get("project_root", ".")
        self.project_root = self._resolve_path(raw_project_root, self.config_base_dir)

        advanced = config.get("advanced", {}) or {}
        self.dry_run = bool(cli_dry_run or advanced.get("dry_run", False))
        self.verbose = bool(advanced.get("verbose", True))
        self.create_backup_enabled = bool(advanced.get("create_backup", True))
        self.rollback_on_failure = bool(advanced.get("rollback_on_failure", True))
        self.backup_location_raw = advanced.get("backup_location", "../backup")
        self.exclude_patterns = tuple((advanced.get("exclude_patterns", []) or []) + list(DEFAULT_EXCLUDES))

        content_cfg = config.get("content", {}) or {}
        self.custom_patterns = content_cfg.get("custom_patterns", []) or []

        metadata_cfg = config.get("metadata", {}) or {}
        self.update_readme = bool(metadata_cfg.get("update_readme", True))
        self.update_changelog = bool(metadata_cfg.get("update_changelog", False))
        self.update_license = bool(metadata_cfg.get("update_license", False))
        self.metadata_project = metadata_cfg.get("project", {}) or {}

        self.package_old_slash = self.package_old.replace(".", "/")
        self.package_new_slash = self.package_new.replace(".", "/")
        self.brand_pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(self.brand_old)}(?![A-Za-z0-9_])")

        self.report = ExecutionReport()
        self.backup_path: Optional[Path] = None
        self.backup_outside_root = True

    @staticmethod
    def _resolve_path(path_text: str, base_dir: Path) -> Path:
        candidate = Path(path_text)
        if candidate.is_absolute():
            return candidate.resolve()
        return (base_dir / candidate).resolve()

    def _log(self, message: str):
        if self.verbose:
            print(message)

    def _warn(self, message: str):
        self.report.warnings.append(message)
        print(f"[WARN] {message}")

    def validate_config(self) -> Tuple[bool, List[str]]:
        """Validate configuration before proceeding."""
        errors: List[str] = []

        if not self.brand_new:
            errors.append("New brand name is required")
        elif not re.fullmatch(r"[a-z0-9-]+", self.brand_new):
            errors.append("New brand name must match [a-z0-9-]+")

        if not self.package_new:
            errors.append("New package name is required")
        elif not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*", self.package_new):
            errors.append("New package name is invalid")

        if not self.project_root.exists():
            errors.append(f"Project root does not exist: {self.project_root}")
        elif not (self.project_root / "pom.xml").exists():
            self._warn(f"No root pom.xml found under: {self.project_root}")

        if self.brand_old == self.brand_new:
            self._warn("Old and new brand names are identical; brand replacement will be skipped.")

        if self.package_old == self.package_new:
            self._warn("Old and new package names are identical; package replacement will be skipped.")

        return len(errors) == 0, errors

    def _backup_base_dir(self) -> Path:
        configured = Path(self.backup_location_raw)
        if configured.is_absolute():
            return configured
        return (self.project_root / configured).resolve()

    def create_backup(self) -> Optional[Path]:
        """Create a backup of the project before modifications."""
        if not self.create_backup_enabled:
            self._log("Backup skipped: create_backup=false")
            return None

        if self.dry_run:
            self._log("Backup skipped in dry-run mode")
            return None

        backup_base = self._backup_base_dir()
        backup_base.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = backup_base / f"{self.project_root.name}-{timestamp}"

        self.backup_outside_root = not _is_relative_to(backup_path, self.project_root)
        if not self.backup_outside_root and self.rollback_on_failure:
            self._warn("Backup path is inside project root; auto-rollback will be disabled.")

        self._log(f"Creating backup at: {backup_path}")
        shutil.copytree(
            self.project_root,
            backup_path,
            ignore=shutil.ignore_patterns(".git", "target", "node_modules", ".idea", "*.class"),
        )
        self.backup_path = backup_path
        return backup_path

    def _should_skip_file(self, file_path: Path) -> bool:
        try:
            rel = file_path.resolve().relative_to(self.project_root.resolve()).as_posix()
        except ValueError:
            return True

        for pattern in self.exclude_patterns:
            normalized = pattern.replace("\\", "/")
            if fnmatch.fnmatch(rel, normalized) or fnmatch.fnmatch(file_path.name, normalized):
                return True
        return False

    def _iter_files(self, patterns: Sequence[str]) -> Iterable[Path]:
        seen: Set[Path] = set()
        for pattern in patterns:
            for file_path in self.project_root.rglob(pattern):
                if not file_path.is_file():
                    continue
                resolved = file_path.resolve()
                if resolved in seen or self._should_skip_file(resolved):
                    continue
                seen.add(resolved)
                yield resolved

    def _write_file(self, file_path: Path, content: str):
        rel = file_path.relative_to(self.project_root).as_posix()
        if self.dry_run:
            self._log(f"[DRY-RUN] Would update: {rel}")
            return
        file_path.write_text(content, encoding="utf-8")
        self._log(f"Updated: {rel}")

    def _merge_dir_contents(self, old_path: Path, new_path: Path, old_name: str, new_name: str):
        """Merge old directory contents into existing target directory."""
        rel_message = f"{old_name} => {new_name} (merge)"
        if self.dry_run:
            self._log(f"[DRY-RUN] Would merge directory: {rel_message}")
            self.report.dirs_renamed.append(rel_message)
            return

        for child in old_path.iterdir():
            target = new_path / child.name
            if target.exists():
                try:
                    rel_target = target.relative_to(self.project_root).as_posix()
                except ValueError:
                    rel_target = str(target)
                self._warn(f"Merge conflict, keeping existing path: {rel_target}")
                continue
            shutil.move(str(child), str(target))

        try:
            old_path.rmdir()
        except OSError:
            self._warn(f"Directory not empty after merge: {old_name}")

        self._log(f"Merged: {rel_message}")
        self.report.dirs_renamed.append(rel_message)

    @staticmethod
    def _protect_literals(content: str) -> Tuple[str, Dict[str, str]]:
        placeholder_map: Dict[str, str] = {}
        protected = content
        for idx, literal in enumerate(PROTECTED_LITERALS):
            placeholder = f"__CN_PROTECT_{idx}__"
            protected = protected.replace(literal, placeholder)
            placeholder_map[placeholder] = literal
        return protected, placeholder_map

    @staticmethod
    def _restore_literals(content: str, placeholder_map: Dict[str, str]) -> str:
        restored = content
        for placeholder, literal in placeholder_map.items():
            restored = restored.replace(placeholder, literal)
        return restored

    def rename_directories(self):
        """Rename directories from continew-* to custom brand."""
        self._log("\n=== Renaming Directories ===")

        normalized: List[Tuple[str, str]] = []
        for dir_config in self.directories:
            old_name = (dir_config.get("from") or "").strip().replace("\\", "/")
            new_name = (dir_config.get("to") or "").strip().replace("\\", "/")
            if old_name and new_name:
                normalized.append((old_name, new_name))

        normalized.sort(key=lambda pair: len(pair[0].split("/")), reverse=True)

        for old_name, new_name in normalized:
            old_path = (self.project_root / old_name).resolve()
            new_path = (self.project_root / new_name).resolve()

            if not old_path.exists():
                self._warn(f"Directory not found: {old_name}")
                continue
            if new_path.exists():
                if old_path.is_dir() and new_path.is_dir():
                    self._merge_dir_contents(old_path, new_path, old_name, new_name)
                    continue
                self._warn(f"Target already exists: {new_name}")
                continue

            rel_message = f"{old_name} -> {new_name}"
            if self.dry_run:
                self._log(f"[DRY-RUN] Would rename: {rel_message}")
            else:
                new_path.parent.mkdir(parents=True, exist_ok=True)
                old_path.rename(new_path)
                self._log(f"Renamed: {rel_message}")
            self.report.dirs_renamed.append(rel_message)

    def _replace_in_file_literal(self, file_path: Path, replacements: Sequence[Tuple[str, str]]) -> Tuple[bool, int]:
        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError) as exc:
            self._warn(f"Skipping {file_path}: {exc}")
            return False, 0

        changed = False
        replacement_count = 0
        updated = content
        for old_text, new_text in replacements:
            if not old_text or old_text == new_text:
                continue
            count = updated.count(old_text)
            if count:
                updated = updated.replace(old_text, new_text)
                replacement_count += count
                changed = True

        if changed:
            self._write_file(file_path, updated)
        return changed, replacement_count

    def replace_package_paths(self):
        """Replace package references while preserving starter namespaces."""
        self._log("\n=== Replacing Package Paths ===")

        replacements = (
            (self.package_old, self.package_new),
            (self.package_old_slash, self.package_new_slash),
        )
        for file_path in self._iter_files(PACKAGE_PATTERNS):
            self.report.files_scanned += 1
            changed, count = self._replace_in_file_literal(file_path, replacements)
            if changed:
                self.report.files_updated += 1
                self.report.replacements += count

    def replace_brand_content(self):
        """Replace brand names while preserving protected literals."""
        self._log("\n=== Replacing Brand Content ===")
        if self.brand_old == self.brand_new:
            return

        for file_path in self._iter_files(DEFAULT_TEXT_PATTERNS):
            self.report.files_scanned += 1
            try:
                content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError) as exc:
                self._warn(f"Skipping {file_path}: {exc}")
                continue

            protected, placeholder_map = self._protect_literals(content)
            replaced, count = self.brand_pattern.subn(self.brand_new, protected)
            updated = self._restore_literals(replaced, placeholder_map)

            if count > 0 and updated != content:
                self._write_file(file_path, updated)
                self.report.files_updated += 1
                self.report.replacements += count

    def apply_custom_patterns(self):
        """Apply user-defined custom replacement patterns."""
        if not self.custom_patterns:
            return

        self._log("\n=== Applying Custom Patterns ===")
        for item in self.custom_patterns:
            old_text = (item.get("from") or "").strip()
            new_text = (item.get("to") or "").strip()
            file_patterns = item.get("file_patterns") or DEFAULT_TEXT_PATTERNS
            if not old_text:
                continue

            for file_path in self._iter_files(file_patterns):
                self.report.files_scanned += 1
                changed, count = self._replace_in_file_literal(file_path, ((old_text, new_text),))
                if changed:
                    self.report.files_updated += 1
                    self.report.replacements += count

    @staticmethod
    def _remove_module_line(xml_text: str, module_name: str) -> Tuple[str, int]:
        pattern = re.compile(rf"\n[ \t]*<module>{re.escape(module_name)}</module>[ \t]*")
        return pattern.subn("", xml_text)

    @staticmethod
    def _remove_dependency_block(xml_text: str, artifact_id: str) -> Tuple[str, int]:
        pattern = re.compile(
            rf"\n?[ \t]*<dependency>\s*.*?<artifactId>{re.escape(artifact_id)}</artifactId>.*?</dependency>\s*",
            flags=re.DOTALL,
        )
        return pattern.subn("\n", xml_text)

    def _update_pom_for_removed_module(self, artifact_id: str):
        pom_files = list(self.project_root.rglob("pom.xml"))
        for pom_file in pom_files:
            if self._should_skip_file(pom_file):
                continue
            try:
                content = pom_file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError) as exc:
                self._warn(f"Skipping pom update {pom_file}: {exc}")
                continue

            updated = content
            updated, module_removed = self._remove_module_line(updated, artifact_id)
            updated, dep_removed = self._remove_dependency_block(updated, artifact_id)
            if updated != content and (module_removed > 0 or dep_removed > 0):
                self._write_file(pom_file, updated)
                rel = pom_file.relative_to(self.project_root).as_posix()
                self.report.pom_updated.append(rel)

    def _resolve_module_target(self, module_name: str) -> Optional[Path]:
        normalized = module_name.strip().replace("\\", "/")
        candidates = [
            self.project_root / normalized,
            self.project_root / KNOWN_MODULE_PATHS.get(normalized, ""),
        ]

        if "/" not in normalized:
            if normalized.startswith("continew-plugin-"):
                candidates.append(self.project_root / "continew-plugin" / normalized)
            if normalized.startswith("continew-extension-"):
                candidates.append(self.project_root / "continew-extension" / normalized)

        for candidate in candidates:
            if candidate and candidate.exists():
                return candidate.resolve()
        return None

    def remove_modules(self):
        """Remove specified modules and synchronize pom references."""
        self._log("\n=== Removing Modules ===")

        for module_name in self.modules_remove:
            module_path = self._resolve_module_target(module_name)
            if not module_path:
                self._warn(f"Module not found: {module_name}")
                continue

            artifact_id = module_path.name
            rel = module_path.relative_to(self.project_root).as_posix()
            if self.dry_run:
                self._log(f"[DRY-RUN] Would remove module: {rel}")
            else:
                shutil.rmtree(module_path)
                self._log(f"Removed module: {rel}")
            self.report.dirs_removed.append(rel)

            self._update_pom_for_removed_module(artifact_id)

    def update_project_metadata(self):
        """Update basic project metadata files."""
        self._log("\n=== Updating Project Metadata ===")
        project_name = (self.metadata_project.get("name") or "").strip()
        project_desc = (self.metadata_project.get("description") or "").strip()

        if self.update_readme:
            readme_path = self.project_root / "README.md"
            if readme_path.exists():
                try:
                    content = readme_path.read_text(encoding="utf-8")
                    updated = content
                    if project_name:
                        updated = updated.replace("ContiNew Admin", project_name)
                    if project_desc:
                        updated = updated.replace(
                            "持续迭代优化的前后端分离中后台管理系统框架，开箱即用，持续提供舒适的开发体验。",
                            project_desc,
                        )
                    if updated != content:
                        self._write_file(readme_path, updated)
                        self.report.files_updated += 1
                except (UnicodeDecodeError, PermissionError) as exc:
                    self._warn(f"Skipping metadata update for README.md: {exc}")

        if self.update_changelog:
            changelog = self.project_root / "CHANGELOG.md"
            if changelog.exists():
                self._log("update_changelog=true: please verify if historical changelog should be retained.")

        if self.update_license:
            self._log("update_license=true: review LICENSE holder fields manually.")

    def post_validate(self):
        """Basic post checks to catch obvious replacement gaps."""
        self._log("\n=== Post Validation ===")
        remaining_old_package = 0

        for file_path in self._iter_files(PACKAGE_PATTERNS):
            try:
                content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            remaining_old_package += content.count(self.package_old)

        if remaining_old_package > 0:
            self._warn(f"Found {remaining_old_package} occurrences of old package: {self.package_old}")
        else:
            self._log("No old package references detected.")

        self._validate_child_modules_exist()

    @staticmethod
    def _extract_module_names(pom_content: str) -> List[str]:
        return [name.strip() for name in re.findall(r"<module>\s*([^<\s]+)\s*</module>", pom_content)]

    def _validate_child_modules_exist(self):
        """Validate that all child modules declared in pom.xml physically exist."""
        missing_entries: List[str] = []

        for pom_file in self.project_root.rglob("pom.xml"):
            if self._should_skip_file(pom_file):
                continue
            try:
                content = pom_file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError) as exc:
                self._warn(f"Skipping module path validation for {pom_file}: {exc}")
                continue

            module_names = self._extract_module_names(content)
            if not module_names:
                continue

            for module_name in module_names:
                module_dir = (pom_file.parent / module_name).resolve()
                if module_dir.exists():
                    continue

                pom_rel = pom_file.relative_to(self.project_root).as_posix()
                try:
                    module_rel = module_dir.relative_to(self.project_root).as_posix()
                except ValueError:
                    module_rel = str(module_dir)

                message = f"{pom_rel} -> missing module dir: {module_rel}"
                missing_entries.append(message)
                self._warn(message)

        self.report.missing_modules.extend(missing_entries)

    def try_rollback(self):
        if self.dry_run or not self.rollback_on_failure or not self.backup_path:
            return
        if not self.backup_outside_root:
            self._warn("Skipping auto rollback because backup is inside project root.")
            return

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        failed_path = self.project_root.parent / f"{self.project_root.name}-failed-{timestamp}"
        try:
            if self.project_root.exists():
                shutil.move(str(self.project_root), str(failed_path))
            shutil.copytree(self.backup_path, self.project_root)
            self._warn(f"Rollback completed from backup: {self.backup_path}")
            self._warn(f"Failed state moved to: {failed_path}")
        except Exception as exc:  # pylint: disable=broad-except
            self._warn(f"Auto rollback failed: {exc}")
            self._warn(f"Manual restore from backup: {self.backup_path}")

    def print_summary(self):
        print("\n" + "=" * 60)
        print("Execution Summary")
        print("=" * 60)
        print(f"Dry run: {self.dry_run}")
        print(f"Files scanned: {self.report.files_scanned}")
        print(f"Files updated: {self.report.files_updated}")
        print(f"Replacement count: {self.report.replacements}")
        print(f"Directories renamed: {len(self.report.dirs_renamed)}")
        print(f"Directories removed: {len(self.report.dirs_removed)}")
        print(f"POM files updated: {len(self.report.pom_updated)}")
        print(f"Missing module paths: {len(self.report.missing_modules)}")
        if self.report.warnings:
            print(f"Warnings: {len(self.report.warnings)}")
        print("=" * 60)

    def run(self) -> bool:
        """Execute the full initialization process."""
        print(f"\n{'=' * 60}")
        print("ContiNew Project Initializer")
        print(f"{'=' * 60}")
        print(f"Brand: {self.brand_old} -> {self.brand_new}")
        print(f"Package: {self.package_old} -> {self.package_new}")
        print(f"Project Root: {self.project_root}")
        print(f"Dry Run: {self.dry_run}")
        print(f"{'=' * 60}\n")

        is_valid, errors = self.validate_config()
        if not is_valid:
            print("Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False

        try:
            self.create_backup()
            self.remove_modules()
            self.rename_directories()
            self.replace_package_paths()
            self.replace_brand_content()
            self.apply_custom_patterns()
            self.update_project_metadata()
            self.post_validate()
        except Exception as exc:  # pylint: disable=broad-except
            self._warn(f"Execution failed: {exc}")
            self.try_rollback()
            self.print_summary()
            return False

        self.print_summary()
        print("\nNext steps:")
        print("1. Review changes in your IDE")
        print("2. Run: mvn clean install (backend)")
        print("3. Validate startup and key APIs")
        return True


def load_config(config_file: str) -> Dict:
    """Load configuration from YAML file."""
    with open(config_file, "r", encoding="utf-8") as file_obj:
        loaded = yaml.safe_load(file_obj)
    return loaded or {}


def interactive_mode() -> Dict:
    """Run interactive configuration mode."""
    print("\n=== ContiNew Project Initialization - Interactive Mode ===\n")

    config = {
        "brand": {"old": "continew"},
        "package": {"old": "top.continew.admin"},
        "directories": {"rename": []},
        "modules": {"remove": []},
        "project_root": ".",
        "advanced": {"create_backup": True, "dry_run": False, "verbose": True},
    }

    config["brand"]["new"] = input("Enter new brand name (e.g., mycompany): ").strip().lower()
    config["package"]["new"] = input("Enter new package name (e.g., com.mycompany.admin): ").strip()
    config["project_root"] = input("Project root path (default .): ").strip() or "."

    remove_schedule = input("Remove schedule-server module? (y/N): ").strip().lower()
    if remove_schedule == "y":
        config["modules"]["remove"].append("continew-extension-schedule-server")

    brand_new = config["brand"]["new"]
    directories = [
        ("continew-admin", f"{brand_new}-admin"),
        ("continew-server", f"{brand_new}-server"),
        ("continew-system", f"{brand_new}-system"),
        ("continew-common", f"{brand_new}-common"),
        ("continew-plugin", f"{brand_new}-plugin"),
        ("continew-extension", f"{brand_new}-extension"),
        ("continew-plugin/continew-plugin-open", f"{brand_new}-plugin/{brand_new}-plugin-open"),
        ("continew-plugin/continew-plugin-tenant", f"{brand_new}-plugin/{brand_new}-plugin-tenant"),
        ("continew-plugin/continew-plugin-schedule", f"{brand_new}-plugin/{brand_new}-plugin-schedule"),
        ("continew-plugin/continew-plugin-generator", f"{brand_new}-plugin/{brand_new}-plugin-generator"),
    ]
    if remove_schedule != "y":
        directories.append(
            (
                "continew-extension/continew-extension-schedule-server",
                f"{brand_new}-extension/{brand_new}-extension-schedule-server",
            )
        )
    for old_dir, new_dir in directories:
        config["directories"]["rename"].append({"from": old_dir, "to": new_dir})

    return config


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize ContiNew Admin based project")
    parser.add_argument("--config", "-c", help="Configuration file (YAML)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")
    args = parser.parse_args()

    if args.interactive:
        config = interactive_mode()
        config_file = None
    elif args.config:
        config_file = Path(args.config).resolve()
        config = load_config(str(config_file))
    else:
        parser.print_help()
        return 1

    initializer = ContiNewInitializer(config=config, config_file=config_file, cli_dry_run=args.dry_run)
    success = initializer.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
