#!/usr/bin/env python3
"""
Create Project from Template

Copies a template project to a new location and runs initialization with the given config.
Supports ContiNew Admin, RuoYi, and other Java admin frameworks.

Usage:
    python create_project.py --template /path/to/template --config my-config.yaml --output ./my-new-project

Examples:
    python create_project.py --template ./RuoYi-master --config ruoyi-config.yaml --output ./my-admin
    python create_project.py --template ./continew-admin --config continew-config.yaml --output ./company-admin

Note: This is a skeleton implementation. Full logic: copy template -> set project_root -> run init_project.
"""

import argparse
import shutil
import tempfile
from pathlib import Path


def _script_dir() -> Path:
    """Get directory containing this script."""
    return Path(__file__).resolve().parent


def copy_template(template_path: Path, output_path: Path) -> bool:
    """
    Copy template directory to output path.
    Excludes .git, target, node_modules, __pycache__.
    """
    if not template_path.exists():
        print(f"Error: Template path does not exist: {template_path}")
        return False

    if output_path.exists():
        print(f"Error: Output path already exists: {output_path}")
        return False

    exclude_dirs = {'.git', 'target', 'node_modules', '__pycache__', '.idea', '*.iml'}

    def ignore_patterns(directory, files):
        ignored = []
        for f in files:
            full_path = Path(directory) / f
            if full_path.is_dir() and f in exclude_dirs:
                ignored.append(f)
            elif f.endswith('.iml'):
                ignored.append(f)
        return ignored

    print(f"Copying template from {template_path} to {output_path}...")
    shutil.copytree(template_path, output_path, ignore=ignore_patterns)
    print("Copy complete.")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Create a new project from template and run initialization'
    )
    parser.add_argument('--template', '-t', required=True, help='Path to template project directory')
    parser.add_argument('--config', '-c', required=True, help='Configuration file (YAML)')
    parser.add_argument('--output', '-o', required=True, help='Output directory for new project')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without modifying; copies to temp dir then removes')
    parser.add_argument('--verify', action='store_true', help='Run build verify_command after init')

    args = parser.parse_args()

    template_path = Path(args.template).resolve()
    output_path = Path(args.output).resolve()
    config_path = Path(args.config).resolve()

    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        return 1

    # For dry-run: use temp dir so we don't create output; otherwise use output_path
    if args.dry_run:
        parent_tmp = Path(tempfile.mkdtemp(prefix="create_project_dryrun_"))
        work_dir = parent_tmp / "project"
        try:
            if not copy_template(template_path, work_dir):
                shutil.rmtree(parent_tmp, ignore_errors=True)
                return 1
            project_root = str(work_dir)
        except Exception as e:
            shutil.rmtree(work_dir, ignore_errors=True)
            print(f"Error during dry-run: {e}")
            return 1
    else:
        if not copy_template(template_path, output_path):
            return 1
        project_root = str(output_path)

    # Step 2: Run init_project with config
    import yaml

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}

    config['project_root'] = project_root

    if args.dry_run:
        config.setdefault('advanced', {})['dry_run'] = True
        config.setdefault('advanced', {})['create_backup'] = False

    # Merge framework preset when framework is set in config
    fw = config.get('framework')
    if fw:
        from init_project import load_presets, merge_preset
        presets = load_presets()
        preset = presets.get(fw, {})
        if preset and config.get('brand', {}).get('new'):
            config = merge_preset(config, preset, config['brand']['new'])

    from init_project import ProjectInitializer

    initializer = ProjectInitializer(config)
    success = initializer.run()

    if args.dry_run:
        shutil.rmtree(work_dir, ignore_errors=True)
        print('\n[Dry-run complete. Run without --dry-run to apply.]')

    if success and not args.dry_run and args.verify:
        verify_cmd = config.get('build', {}).get('verify_command')
        if verify_cmd:
            import subprocess
            print(f"\n=== Running verify: {verify_cmd} ===")
            subprocess.run(verify_cmd, shell=True, cwd=project_root)

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
