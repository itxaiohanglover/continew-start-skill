#!/usr/bin/env python3
"""
Project Analyzer - Discovery-driven configuration generator

Scans a Java/Python/Node project directory to infer brand, package, directories, and cap_old.
Outputs a config draft YAML and a Markdown checklist for user review before execution.

Usage:
    python analyze_project.py --path /path/to/project [--output report.yaml] [--format yaml|markdown|both]
"""

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple, Optional, Any


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def find_root_pom(project_root: Path) -> Optional[Path]:
    """Find root pom.xml (has modules or is the only pom in project)."""
    poms = list(project_root.rglob("pom.xml"))
    if not poms:
        return None
    # Prefer pom at project root
    root_pom = project_root / "pom.xml"
    if root_pom.exists():
        return root_pom
    # Else take one that defines modules (likely root)
    for p in poms:
        try:
            tree = ET.parse(p)
            root = tree.getroot()
            ns = {"m": "http://maven.apache.org/POM/4.0.0"}
            modules = root.find("m:modules", ns)
            if modules is not None and list(modules):
                return p
        except ET.ParseError:
            continue
    return poms[0]


def parse_pom(pom_path: Path) -> Dict:
    """Parse pom.xml and extract groupId, artifactId, modules."""
    result = {"groupId": "", "artifactId": "", "modules": []}
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
        ns = {"m": "http://maven.apache.org/POM/4.0.0"}

        def get_text(elem):
            return (elem.text or "").strip() if elem is not None else ""

        def find_el(path):
            e = root.find(f"m:{path}", ns)
            return e if e is not None else root.find(path)

        g = find_el("groupId")
        a = find_el("artifactId")
        result["groupId"] = get_text(g)
        result["artifactId"] = get_text(a)

        parent = find_el("parent")
        if parent is not None and not result["groupId"]:
            pg = parent.find("m:groupId", ns)
            if pg is None:
                pg = parent.find("groupId")
            result["groupId"] = get_text(pg)

        modules_el = find_el("modules")
        if modules_el is not None:
            for m in modules_el.findall("m:module", ns) or modules_el.findall("module"):
                mod = get_text(m)
                if mod:
                    result["modules"].append(mod)
    except (ET.ParseError, OSError) as e:
        result["_error"] = str(e)
    return result


def infer_brand_from_pyproject(project_root: Path) -> str:
    """Extract brand from pyproject.toml [project]name (e.g. lightrag-hku -> lightrag)."""
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return ""
    try:
        content = pyproject.read_text(encoding="utf-8")
        # Simple line-based parse for [project] name = "xxx"
        in_project = False
        for line in content.splitlines():
            line = line.strip()
            if line == "[project]":
                in_project = True
                continue
            if in_project and line.startswith("["):
                break
            if in_project and line.startswith("name"):
                # name = "lightrag-hku" or name = 'lightrag-hku'
                m = re.search(r'name\s*=\s*["\']([^"\']+)["\']', line)
                if m:
                    name = m.group(1).strip()
                    parts = re.split(r"[-_]", name)
                    for p in parts:
                        if len(p) >= 2 and p.isalpha():
                            return p.lower()
                    return parts[0].lower() if parts else ""
        return ""
    except (OSError, UnicodeDecodeError):
        return ""


def infer_brand_from_package_json(project_root: Path) -> str:
    """Extract brand from package.json name (e.g. lightrag-webui -> lightrag)."""
    pkg = project_root / "package.json"
    if not pkg.exists():
        return ""
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
        name = data.get("name", "")
        if isinstance(name, str):
            parts = re.split(r"[-_/]", name)
            for p in parts:
                if len(p) >= 2 and p.replace(".", "").isalnum():
                    return p.lower()
            return parts[0].lower() if parts else ""
        return ""
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return ""


def infer_package_from_python(project_root: Path) -> Tuple[str, int]:
    """Infer main package from Python structure: top-level dirs with __init__.py, or from imports."""
    packages = []
    # Top-level dirs that look like packages (have __init__.py)
    for d in project_root.iterdir():
        if not d.is_dir() or d.name.startswith("."):
            continue
        if d.name in ("node_modules", "venv", ".venv", "dist", "build", "target"):
            continue
        if (d / "__init__.py").exists():
            packages.append(d.name)
    if packages:
        best = max(packages, key=lambda p: _count_python_imports(project_root, p))
        return best, len(packages)

    # Fallback: most common top-level import in from xxx import
    imports = []
    for pf in project_root.rglob("*.py"):
        if any(x in pf.parts for x in ("node_modules", ".venv", "venv")):
            continue
        try:
            content = pf.read_text(encoding="utf-8")
            for m in re.finditer(r"^\s*from\s+([\w.]+)\s+import", content, re.MULTILINE):
                top = m.group(1).split(".")[0]
                if top not in ("", "importlib"):
                    imports.append(top)
        except (UnicodeDecodeError, OSError):
            continue
    if imports:
        c = Counter(imports)
        return c.most_common(1)[0][0], c.most_common(1)[0][1]
    return "", 0


def _count_python_imports(project_root: Path, pkg: str) -> int:
    """Count how often pkg is imported."""
    count = 0
    for pf in project_root.rglob("*.py"):
        if any(x in pf.parts for x in ("node_modules", ".venv", "venv")):
            continue
        try:
            content = pf.read_text(encoding="utf-8")
            count += len(re.findall(rf"(?m)^\s*(?:from\s+{re.escape(pkg)}[\s.]|import\s+{re.escape(pkg)}\b)", content))
        except (UnicodeDecodeError, OSError):
            pass
    return count


def infer_entry_points_from_pyproject(project_root: Path) -> List[str]:
    """Parse [project.scripts] from pyproject.toml to get entry points like lightrag-server."""
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return []
    result = []
    try:
        content = pyproject.read_text(encoding="utf-8")
        in_scripts = False
        for line in content.splitlines():
            if "[project.scripts]" in line:
                in_scripts = True
                continue
            if in_scripts and line.startswith("["):
                break
            if in_scripts and "=" in line:
                m = re.match(r"^\s*([\w-]+)\s*=", line)
                if m:
                    result.append(m.group(1))
        return result
    except (OSError, UnicodeDecodeError):
        return []


def infer_package_from_java(project_root: Path) -> Tuple[str, int]:
    """Extract package declarations from Java files. Returns (common_prefix, count)."""
    packages = []
    for jf in project_root.rglob("*.java"):
        if "target" in jf.parts or "node_modules" in jf.parts:
            continue
        try:
            content = jf.read_text(encoding="utf-8")
            m = re.search(r"^\s*package\s+([\w.]+)\s*;", content, re.MULTILINE)
            if m:
                pkg = m.group(1).strip()
                packages.append(pkg)
        except (UnicodeDecodeError, OSError):
            continue
    if not packages:
        return "", 0
    # Most frequent 2-3 segment prefix (org.jeecg, me.zhengjie)
    prefix_counts = Counter()
    for p in packages:
        parts = p.split(".")
        for n in [2, 3]:
            if len(parts) >= n:
                prefix_counts[".".join(parts[:n])] += 1
    if prefix_counts:
        best = prefix_counts.most_common(1)[0]
        return best[0], best[1]
    return packages[0].split(".")[0], 1


def infer_brand_from_artifact(artifactId: str) -> str:
    """Infer brand from artifactId (e.g. jeecg-boot-parent -> jeecg)."""
    if not artifactId:
        return ""
    # jeecg-boot-parent, ruoyi-admin -> first segment
    parts = artifactId.replace("_", "-").split("-")
    for p in parts:
        if len(p) >= 2 and p.isalpha():
            return p.lower()
    return parts[0].lower() if parts else ""


def infer_brand_from_dirs(project_root: Path) -> str:
    """Infer brand from directory names (e.g. jeecg-boot, ruoyi-admin, lightrag_webui)."""
    prefixes = []
    for d in project_root.rglob("*"):
        if not d.is_dir() or d.name.startswith("."):
            continue
        if "target" in d.parts or "node_modules" in d.parts:
            continue
        # Match pattern xxx-yyy or xxx_yyy
        for sep in ("-", "_"):
            if sep in d.name:
                pre = d.name.split(sep)[0].lower()
                if len(pre) >= 2 and pre.isalpha():
                    prefixes.append(pre)
                break
    if not prefixes:
        return ""
    return Counter(prefixes).most_common(1)[0][0]


def find_brand_directories(project_root: Path, brand: str) -> List[Dict]:
    """Find all dirs whose name contains brand. Returns [{from, to}] for init, shallow-first.
    Each 'from' is the path as it will be when init reaches that step (parents already renamed)."""
    if not brand:
        return []
    candidates = []
    try:
        rel_project = project_root.resolve()
        for d in project_root.rglob("*"):
            if not d.is_dir():
                continue
            try:
                rel = d.relative_to(rel_project)
            except ValueError:
                continue
            if brand.lower() not in d.name.lower():
                continue
            new_name = d.name.replace(brand, "{new_brand}").replace(
                brand.capitalize(), "{new_brand}"
            )
            if "{new_brand}" not in new_name:
                idx = d.name.lower().find(brand.lower())
                new_name = d.name[:idx] + "{new_brand}" + d.name[idx + len(brand):]
            candidates.append((str(rel).replace("\\", "/"), new_name))
    except OSError:
        pass
    candidates.sort(key=lambda x: x[0].count("/"))

    renames = []
    applied = []  # (from, to) - paths after previous renames
    for orig_path, new_name_tmpl in candidates:
        from_path = orig_path
        for f, t in applied:
            if from_path == f or from_path.startswith(f + "/"):
                from_path = from_path.replace(f, t, 1)
        if "/" in from_path:
            parent = from_path.rsplit("/", 1)[0]
            to_path = parent + "/" + new_name_tmpl
        else:
            to_path = new_name_tmpl
        renames.append({"from": from_path, "to": to_path})
        applied.append((from_path, to_path))
    return renames


def find_cap_candidates(project_root: Path, brand: str) -> List[Tuple[str, int]]:
    """Find PascalCase brand candidates. Prefer product names over class names (e.g. JeecgBoot > JeecgBootException)."""
    if not brand:
        return []
    candidates: Counter = Counter()
    skip = {"target", "node_modules", ".git", "venv", ".venv"}
    # Weight README/docs higher (product name) vs Java/Python/TS (class names)
    for ext, weight in [("*.md", 3), ("*.yml", 2), ("*.yaml", 2), ("*.java", 1), ("*.py", 1), ("*.ts", 1), ("*.tsx", 1)]:
        for f in project_root.rglob(ext):
            if any(d in f.parts for d in skip):
                continue
            try:
                content = f.read_text(encoding="utf-8")
                for m in re.finditer(r"\b([A-Z][a-z]*(?:[A-Z][a-z]*)*)\b", content):
                    word = m.group(1)
                    if brand.lower() in word.lower() and len(word) >= len(brand):
                        candidates[word] += weight
            except (UnicodeDecodeError, OSError):
                continue
    most = candidates.most_common(10)
    if not most:
        return []
    # Prefer product-like names (JeecgBoot, RuoYi) over class names (JeecgBootException)
    class_suffixes = ("Exception", "Controller", "Service", "Impl", "Config", "Mapper", "Demo", "Main", "Order")
    product_suffixes = ("Boot", "Boot", "Admin", "Framework")  # Boot weighted
    for word, cnt in most:
        if not any(word.endswith(s) for s in class_suffixes):
            if any(s in word for s in product_suffixes) or len(word) <= 10:
                return [(word, cnt)] + [(w, c) for w, c in most if w != word][:4]
    for word, cnt in most:
        if not any(word.endswith(s) for s in class_suffixes):
            return [(word, cnt)] + [(w, c) for w, c in most if w != word][:4]
    return most[:5]


def discover_content_replacements(
    project_root: Path,
    brand_base: str,
    package_base: str,
    cap_base: str,
    deep_scan: bool = True,
    skip_dirs: set = None,
) -> List[Dict]:
    """
    Scan text files to discover all actual occurrences of brand/package/cap variants.
    Returns list of {from, type} where type is 'package', 'brand', or 'cap'.
    Only keeps pure case variants: s.lower() == base.lower().
    Uses word boundary \\b to avoid false matches.
    """
    if skip_dirs is None:
        skip_dirs = {"target", "node_modules", ".git", "backup"}
    result = []
    seen_from = set()

    def add(from_str: str, rtype: str):
        if from_str and from_str not in seen_from:
            seen_from.add(from_str)
            result.append({"from": from_str, "type": rtype})

    if not brand_base and not package_base:
        return result

    # File patterns to scan (extended for Python/Node/Docker)
    patterns = [
        "*.java", "*.xml", "*.yml", "*.yaml", "*.properties", "*.ftl", "*.sql", "*.md", "*.txt", "*.vm", "*.html",
        "*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.json", "*.toml", "*.ini", "*.sh", "*.tpl",
    ]
    if not deep_scan:
        patterns = ["*.java", "*.yml", "*.xml", "*.py", "*.ts", "*.tsx"]

    text_exts = {p.lstrip("*") for p in patterns}
    _skip = (skip_dirs or set()) | {"venv", ".venv", "__pycache__"}

    for ext in text_exts:
        for f in project_root.rglob(f"*{ext}"):
            if any(d in f.parts for d in _skip):
                continue
            if not f.is_file():
                continue
            try:
                content = f.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue

            # Package: exact match (package declarations, imports)
            if package_base:
                add(package_base, "package")

            # Brand: word-boundary regex, collect actual case variants
            # Type "upper" = ALL_CAPS/UPPER_SNAKE/UPPER_KEBAB -> brand_new.upper()
            # Type "cap" = PascalCase/CamelCase -> cap_new
            # Type "brand" = lowercase/snake_case/kebab-case -> brand_new
            if brand_base:
                escaped = re.escape(brand_base)
                for m in re.finditer(rf"(?i)\b{escaped}\b", content):
                    actual = m.group(0)
                    if actual.lower() == brand_base.lower():
                        # ALL_CAPS: LIGHTRAG, LIGHTRAG_API, LIGHTRAG-API-TOKEN -> upper type
                        if actual.isupper() or re.match(r"^[A-Z][A-Z0-9_\-]*$", actual):
                            rtype = "upper"
                        elif actual[0].isupper() if actual else False:
                            rtype = "cap"
                        else:
                            rtype = "brand"
                        add(actual, rtype)
                # Brand inside UPPER_SNAKE / UPPER_KEBAB (e.g. LIGHTRAG_API, LIGHTRAG-API-TOKEN) -> upper
                for m in re.finditer(rf"(?i)\b({escaped}(?:[_\-][A-Z0-9_\-]+)*)\b", content):
                    actual = m.group(1)
                    if actual.upper() == actual and len(actual) > len(brand_base):
                        add(actual, "upper")
                # Brand as prefix of CamelCase identifiers (e.g. EladminSystemApplicationTests, LightRAGServer)
                for m in re.finditer(rf"(?i)\b({escaped}[A-Za-z][a-zA-Z0-9]*)", content):
                    actual = m.group(1)
                    if actual.lower().startswith(brand_base.lower()) and len(actual) > len(brand_base):
                        # Exclude ALL_CAPS (handled above)
                        if not (actual.upper() == actual):
                            add(actual, "cap")
                # Brand as segment in snake_case / kebab-case (e.g. lightrag_server, lightrag-server)
                for m in re.finditer(rf"(?i)\b({escaped}(?:[_\-][a-z0-9_\-]+)*)\b", content):
                    actual = m.group(1)
                    if ("_" in actual or "-" in actual) and actual != actual.upper():
                        add(actual, "brand")
                # Brand as substring inside camelCase identifiers (e.g. useLightragGraph, LightragPathFilter)
                # Match: optional lowercase prefix + brand + alphanumeric suffix
                for m in re.finditer(rf"(?i)([a-z]*)({escaped})([A-Za-z0-9]*)", content):
                    prefix, brand_part, suffix = m.group(1), m.group(2), m.group(3)
                    if not suffix or suffix[0].isupper() or suffix[0].isdigit():
                        ident = prefix + brand_part + suffix
                        if len(ident) > len(brand_base):
                            if not prefix or (prefix[-1].islower() and len(brand_part) > 0 and brand_part[0].isupper()):
                                add(ident, "cap")

    return result


def discover_file_renames(
    project_root: Path,
    brand_base: str,
    skip_dirs: set = None,
) -> List[Dict]:
    """
    Find all files whose basename contains brand (case-insensitive).
    Returns list of {path, new_name} where path is relative to project_root.
    Covers .java, .sql, .json, .xml, .yml, .yaml, .properties, .md, .html, etc.
    """
    if skip_dirs is None:
        skip_dirs = {"target", "node_modules", ".git", "backup"}
    if not brand_base:
        return []

    result = []
    brand_lower = brand_base.lower()
    text_exts = {
        ".java", ".sql", ".json", ".xml", ".yml", ".yaml", ".properties", ".md", ".html", ".ftl", ".vm", ".txt",
        ".py", ".ts", ".tsx", ".js", ".jsx", ".toml", ".ini", ".sh", ".tpl",
    }
    skip_dirs = skip_dirs or set()
    skip_dirs = skip_dirs | {"venv", ".venv", "__pycache__"}

    for f in project_root.rglob("*"):
        if not f.is_file():
            continue
        if any(d in f.parts for d in skip_dirs):
            continue
        ext = f.suffix.lower()
        is_named_file = f.name.startswith("Dockerfile") or f.name.endswith(".example")
        if ext not in text_exts and not is_named_file:
            continue

        try:
            rel = f.relative_to(project_root)
        except ValueError:
            continue

        rel_str = str(rel).replace("\\", "/")
        base_name = f.name
        if brand_lower not in base_name.lower():
            continue

        # Compute new name: replace brand occurrence with placeholder
        # Use {new_cap} when brand segment is PascalCase/ALL_CAPS (e.g. EladminConfig.java)
        idx = base_name.lower().find(brand_lower)
        if idx >= 0:
            segment = base_name[idx:idx + len(brand_base)]
            placeholder = "{new_cap}" if segment.isupper() or (len(segment) > 0 and segment[0].isupper()) else "{new_brand}"
            new_name = base_name[:idx] + placeholder + base_name[idx + len(brand_base):]
            result.append({"path": rel_str, "new_name": new_name})

    return result


def discover_references_for_renamed_files(
    project_root: Path,
    file_renames: List[Dict],
    brand_base: str,
    skip_dirs: set = None,
) -> List[Dict]:
    """
    For each renamed file, derive the export/symbol name (e.g. useLightragGraph from useLightragGraph.tsx)
    and find references in codebase. Add these symbols to discovered_replacements so imports get updated.
    Returns list of {from, type} to merge into discovered_replacements.
    """
    if skip_dirs is None:
        skip_dirs = {"target", "node_modules", ".git", "backup", "venv", ".venv"}
    result = []
    seen = set()

    for fr in file_renames:
        path = fr.get("path", "")
        base_name = Path(path).stem  # useLightragGraph from useLightragGraph.tsx
        if not base_name or brand_base.lower() not in base_name.lower():
            continue
        if base_name in seen:
            continue
        seen.add(base_name)

        # Grep for import/from/require references to this symbol
        ref_patterns = [
            rf"import\s+{re.escape(base_name)}\b",
            rf"import\s+\{{[^}}]*\b{re.escape(base_name)}\b",
            rf"from\s+[\w./]+import\s+.*\b{re.escape(base_name)}\b",
            rf"require\s*\(\s*[\"'].*{re.escape(base_name)}",
        ]
        found = False
        for pat in ref_patterns:
            for f in project_root.rglob("*"):
                if not f.is_file() or any(d in f.parts for d in skip_dirs):
                    continue
                ext = f.suffix.lower()
                if ext not in (".py", ".ts", ".tsx", ".js", ".jsx", ".vue"):
                    continue
                try:
                    if re.search(pat, f.read_text(encoding="utf-8")):
                        found = True
                        break
                except (UnicodeDecodeError, OSError):
                    continue
            if found:
                break
        # Classify by naming style: path-style (segment-separated or lowercase) -> brand; else cap
        if "_" in base_name or "-" in base_name or (base_name and base_name.islower()):
            rtype = "brand"  # snake_case, kebab-case, or all-lower module path
        elif base_name.upper() == base_name and len(base_name) > len(brand_base):
            rtype = "upper"  # UPPER_SNAKE / UPPER_KEBAB
        else:
            rtype = "cap"    # PascalCase / CamelCase
        if found or len(base_name) > len(brand_base):
            result.append({"from": base_name, "type": rtype})

    return result


def discover_preserve_candidates(project_root: Path, package_old: str, pom: Dict) -> List[str]:
    """
    Discover preserve patterns: groupIds in pom, common third-party prefixes.
    Returns suggestions - user can edit before use.
    """
    suggestions = []
    seen = set()

    def add(s: str):
        if s and s not in seen:
            seen.add(s)
            suggestions.append(s)

    # From pom: all groupIds except project's (and parent)
    project_group = pom.get("groupId", "")
    for pom_path in project_root.rglob("pom.xml"):
        if "target" in pom_path.parts:
            continue
        try:
            tree = ET.parse(pom_path)
            root = tree.getroot()
            ns = {"m": "http://maven.apache.org/POM/4.0.0"}
            for g in root.findall(".//m:groupId", ns) or root.findall(".//groupId"):
                gid = (g.text or "").strip()
                if gid and gid != project_group:
                    # If shares significant prefix with package_old, might need preserve
                    pkg_pre = (package_old or "").split(".")[:2]
                    gid_pre = gid.split(".")[:2]
                    if pkg_pre and gid_pre and pkg_pre[0] == gid_pre[0]:
                        add(gid)
        except (ET.ParseError, OSError):
            continue

    # Known mappings when package shares prefix with common deps
    if package_old:
        pkg_lower = package_old.lower()
        if "jeecg" in pkg_lower:
            add("org.jeecgframework")
            add("jeecg.com")

    return suggestions


def suggest_preserve(project_root: Path, package_old: str) -> List[str]:
    """Suggest preserve patterns - delegates to discover_preserve_candidates."""
    pom = {}
    pom_path = find_root_pom(project_root)
    if pom_path:
        pom = parse_pom(pom_path)
    return discover_preserve_candidates(project_root, package_old, pom)


def detect_build_system(project_root: Path) -> Dict:
    """
    Detect build system and suggest verify command.
    Returns {system, multi_module, modules[], verify_command}.
    """
    result: Dict[str, Any] = {"system": "unknown", "multi_module": False, "modules": [], "verify_command": ""}
    project_root = Path(project_root).resolve()

    if (project_root / "pom.xml").exists():
        result["system"] = "maven"
        pom = parse_pom(project_root / "pom.xml")
        mods = pom.get("modules", [])
        result["modules"] = mods
        result["multi_module"] = len(mods) > 1
        result["verify_command"] = "mvn clean install" if len(mods) > 1 else "mvn clean compile"
    elif (project_root / "build.gradle").exists() or (project_root / "build.gradle.kts").exists():
        result["system"] = "gradle"
        result["verify_command"] = "./gradlew build"
    elif (project_root / "pyproject.toml").exists():
        result["system"] = "python"
        result["verify_command"] = "pip install -e ."
    elif (project_root / "package.json").exists():
        result["system"] = "node"
        result["verify_command"] = "npm install && npm run build"

    return result


def discover_python_dynamic_links(project_root: Path, package_name: str) -> List[Dict[str, Any]]:
    """
    Discover dynamic links between pyproject.toml configuration and Python modules.

    Typical patterns:
      - project.version = { attr = "pkg.__version__" }

    Returns a list of links:
      [{
        "from": {"file": "pyproject.toml", "field": "project.version"},
        "to": {"module_attr": "pkg.__version__"},
        "confidence": "high|medium|low",
        "why": "reason string",
      }, ...]
    """
    links: List[Dict[str, Any]] = []
    pyproject = Path(project_root) / "pyproject.toml"
    if not pyproject.exists():
        return links

    try:
        content = pyproject.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return links

    # Very lightweight TOML pattern matching – we intentionally avoid full TOML parsing
    # to keep this script dependency‑free.
    version_block_re = re.compile(
        r"^\s*version\s*=\s*\{[^}]*attr\s*=\s*[\"']([^\"']+)[\"'][^}]*\}",
        re.MULTILINE,
    )
    for m in version_block_re.finditer(content):
        attr = m.group(1).strip()
        confidence = "medium"
        why_parts = ["pyproject.toml uses version attr"]
        if package_name and attr.startswith(package_name + "."):
            confidence = "high"
            why_parts.append(f"attr starts with inferred package '{package_name}'")
        elif package_name and package_name in attr:
            why_parts.append(f"attr contains inferred package '{package_name}'")
        links.append(
            {
                "from": {"file": "pyproject.toml", "field": "project.version"},
                "to": {"module_attr": attr},
                "confidence": confidence,
                "why": "; ".join(why_parts),
            }
        )

    return links


def get_file_extension_distribution(project_root: Path) -> Dict[str, int]:
    """Count files by extension that might contain references."""
    exts = Counter()
    skip = {"target", "node_modules", ".git", "backup"}
    text_exts = {".java", ".xml", ".yml", ".yaml", ".properties", ".ftl", ".vm", ".html", ".md", ".sql", ".js", ".css"}
    for f in project_root.rglob("*"):
        if not f.is_file():
            continue
        if any(s in f.parts for s in skip):
            continue
        ext = f.suffix.lower()
        if ext in text_exts or ext in {".javai", ".txt", ".json"}:
            exts[ext or "(no ext)"] += 1
    return dict(exts)


def analyze(project_root: Path, deep_scan: bool = True) -> Dict:
    """Run full analysis and return report dict."""
    project_root = Path(project_root).resolve()
    if not project_root.exists():
        return {"error": f"Path does not exist: {project_root}"}

    report: Dict[str, Any] = {
        "project_root": str(project_root),
        "package": {"old": "", "new": "", "confidence": "low"},
        "brand": {"old": "", "new": "", "confidence": "low"},
        "cap_old": "",
        "cap_new": "",
        "cap_candidates": [],
        "directories": {"rename": []},
        "preserve": {"patterns": [], "paths": []},
        "file_types": {},
        "needs_review": [],
        "pom": {},
        "discovered_replacements": [],
        "discovered_file_renames": [],
        "build": {},
        # New, more structured sections for generic consumers (keep backward‑compatible fields above)
        "identity": {
            "brand": {"selected": {}, "candidates": []},
            "package": {"selected": {}, "candidates": []},
            "module_dirs": [],
            "binaries": [],
        },
        "structure": {
            "root": str(project_root),
            "module_dirs": [],
            "has_tests_dir": False,
        },
        "config_files": {
            "python": {"pyproject": ""},
            "node": {"package_json": ""},
            "java": {"pom_xml": ""},
            "ci": {"github_actions": False, "gitlab_ci": False},
            "docker": {"dockerfile": False, "compose": False},
        },
        "occurrences": {
            "total_discovered_replacements": 0,
            "by_type": {},
        },
        "dynamic_links": [],
        "actions": {
            "rename_directories": [],
            "rename_files": [],
            "replace_content": [],
            "update_config": [],
        },
    }

    brand_candidates: List[Dict[str, Any]] = []
    package_candidates: List[Dict[str, Any]] = []

    # 1. Parse pom (Java) or pyproject/package.json (Python/Node)
    pom_path = find_root_pom(project_root)
    if pom_path:
        report["pom"] = parse_pom(pom_path)
        aid = report["pom"].get("artifactId", "")
        report["brand"]["old"] = infer_brand_from_artifact(aid)
        if report["brand"]["old"]:
            report["brand"]["confidence"] = "medium"
            brand_candidates.append(
                {
                    "value": report["brand"]["old"],
                    "source": "maven.artifactId",
                    "confidence": "medium",
                }
            )
        report["config_files"]["java"]["pom_xml"] = str(pom_path)
    if not report["brand"]["old"]:
        b = infer_brand_from_pyproject(project_root)
        if b:
            report["brand"]["old"] = b
            report["brand"]["confidence"] = "medium"
            brand_candidates.append(
                {
                    "value": b,
                    "source": "pyproject.project.name",
                    "confidence": "medium",
                }
            )
        pyproject = project_root / "pyproject.toml"
        if pyproject.exists():
            report["config_files"]["python"]["pyproject"] = str(pyproject)
    if not report["brand"]["old"]:
        b = infer_brand_from_package_json(project_root)
        if b:
            report["brand"]["old"] = b
            report["brand"]["confidence"] = "medium"
            brand_candidates.append(
                {
                    "value": b,
                    "source": "package.json.name",
                    "confidence": "medium",
                }
            )
        pkg_json = project_root / "package.json"
        if pkg_json.exists():
            report["config_files"]["node"]["package_json"] = str(pkg_json)
    if not report["brand"]["old"]:
        b = infer_brand_from_dirs(project_root)
        if b:
            report["brand"]["old"] = b
            report["brand"]["confidence"] = "medium"
            brand_candidates.append(
                {
                    "value": b,
                    "source": "directory_names",
                    "confidence": "medium",
                }
            )

    # 2. Infer package: Java from package declarations, Python from structure/imports
    pkg, count = infer_package_from_java(project_root)
    if pkg:
        report["package"]["old"] = pkg
        report["package"]["confidence"] = "high" if count > 10 else "medium"
        package_candidates.append(
            {
                "value": pkg,
                "source": "java.package",
                "count": count,
                "confidence": report["package"]["confidence"],
            }
        )
    else:
        pkg, count = infer_package_from_python(project_root)
        if pkg:
            report["package"]["old"] = pkg
            report["package"]["confidence"] = "high" if count > 5 else "medium"
            package_candidates.append(
                {
                    "value": pkg,
                    "source": "python.imports",
                    "count": count,
                    "confidence": report["package"]["confidence"],
                }
            )

    # 3. Cap candidates
    report["cap_candidates"] = [
        {"pattern": c[0], "count": c[1]}
        for c in find_cap_candidates(project_root, report["brand"]["old"])
    ]
    if report["cap_candidates"]:
        report["cap_old"] = report["cap_candidates"][0]["pattern"]

    # 4. Directories to rename
    report["directories"]["rename"] = find_brand_directories(project_root, report["brand"]["old"])

    # 5. Preserve suggestions
    preserve_suggestions = suggest_preserve(project_root, report["package"]["old"])
    # 为保持向后兼容，patterns 仍然用于实际替换保护，candidates 仅作为“建议列表”供 AI/用户参考
    report["preserve"]["patterns"] = preserve_suggestions
    report["preserve"]["candidates"] = preserve_suggestions

    # 6. Discover content replacements (brand/package variants)
    if report.get("brand", {}).get("old") or report.get("package", {}).get("old"):
        try:
            report["discovered_replacements"] = discover_content_replacements(
                project_root,
                report["brand"]["old"],
                report["package"]["old"],
                report.get("cap_old", ""),
                deep_scan=deep_scan,
            )
        except Exception:
            report["discovered_replacements"] = []

    # 6b. Discover file renames (files whose name contains brand)
    if report.get("brand", {}).get("old"):
        try:
            report["discovered_file_renames"] = discover_file_renames(
                project_root,
                report["brand"]["old"],
            )
            # 6b2. Discover import references for renamed files, merge into replacements
            refs = discover_references_for_renamed_files(
                project_root,
                report["discovered_file_renames"],
                report["brand"]["old"],
            )
            for r in refs:
                if not any(dr.get("from") == r.get("from") for dr in report["discovered_replacements"]):
                    report["discovered_replacements"].append(r)
        except Exception:
            report["discovered_file_renames"] = []

    # 6c. Detect build system
    report["build"] = detect_build_system(project_root)

    # 7. File types
    report["file_types"] = get_file_extension_distribution(project_root)

    # 8. Needs review
    if not report["package"]["old"]:
        report["needs_review"].append("package.old 未能推断，请手动指定")
    if not report["brand"]["old"]:
        report["needs_review"].append("brand.old 未能推断，请手动指定")
    if report["cap_candidates"] and len(report["cap_candidates"]) > 1:
        report["needs_review"].append(
            f"发现多个 PascalCase 候选: {[c['pattern'] for c in report['cap_candidates']]}，请确认 cap_old"
        )

    # 9. Identity / structure summary
    report["identity"]["brand"]["selected"] = report["brand"]
    report["identity"]["brand"]["candidates"] = brand_candidates
    report["identity"]["package"]["selected"] = report["package"]
    report["identity"]["package"]["candidates"] = package_candidates

    # Module dirs (very lightweight: top-level dirs that look like source roots)
    module_dirs: List[Dict[str, Any]] = []
    for d in project_root.iterdir():
        if not d.is_dir() or d.name.startswith("."):
            continue
        if d.name in ("node_modules", "venv", ".venv", "dist", "build", "target", "backup"):
            continue
        kind = None
        has_init = (d / "__init__.py").exists()
        if has_init:
            kind = "python_package"
        elif (d / "src").exists() or (d / "src/main/java").exists():
            kind = "source_root"
        module_dirs.append(
            {
                "path": str(d.relative_to(project_root)),
                "has_init": has_init,
                "kind": kind or "generic",
            }
        )
    report["identity"]["module_dirs"] = module_dirs
    report["structure"]["module_dirs"] = module_dirs
    report["structure"]["has_tests_dir"] = (project_root / "tests").exists()

    # 10. Binaries / entry points from pyproject (Python) – can be extended for Node later
    entry_points = infer_entry_points_from_pyproject(project_root)
    report["identity"]["binaries"] = [
        {"name": n, "source": "pyproject.scripts"} for n in entry_points
    ]

    # 11. Config files presence (CI / Docker etc.)
    if (project_root / ".github" / "workflows").exists():
        report["config_files"]["ci"]["github_actions"] = True
    if (project_root / ".gitlab-ci.yml").exists():
        report["config_files"]["ci"]["gitlab_ci"] = True
    if (project_root / "Dockerfile").exists():
        report["config_files"]["docker"]["dockerfile"] = True
    if (project_root / "docker-compose.yml").exists():
        report["config_files"]["docker"]["compose"] = True

    # 12. Occurrence summary based on discovered_replacements
    by_type: Dict[str, List[str]] = {}
    for item in report.get("discovered_replacements", []):
        rtype = item.get("type", "brand")
        by_type.setdefault(rtype, []).append(item.get("from", ""))
    report["occurrences"]["total_discovered_replacements"] = len(
        report.get("discovered_replacements", [])
    )
    report["occurrences"]["by_type"] = {
        t: {"values": sorted(set(vals)), "count": len(set(vals))}
        for t, vals in by_type.items()
    }

    # 13. Dynamic links (currently Python/pyproject only; extensible)
    if report.get("package", {}).get("old"):
        try:
            py_links = discover_python_dynamic_links(project_root, report["package"]["old"])
        except Exception:
            py_links = []
        report["dynamic_links"] = py_links

    # 14. Suggested actions layer (for downstream automation)
    #    These are *suggestions* and do not change behavior of existing tools.
    actions = {
        "rename_directories": [],
        "rename_files": [],
        "replace_content": [],
        "update_config": [],
    }
    # Directory renames – medium impact, config+code scope
    for dr in report.get("directories", {}).get("rename", []):
        actions["rename_directories"].append(
            {
                "from": dr.get("from"),
                "to": dr.get("to"),
                "impact": "medium",
                "scope": ["code", "config"],
                "confidence": report.get("brand", {}).get("confidence", "low"),
            }
        )
    # File renames – medium impact, code/doc scope
    for fr in report.get("discovered_file_renames", []):
        actions["rename_files"].append(
            {
                "path": fr.get("path"),
                "new_name": fr.get("new_name"),
                "impact": "medium",
                "scope": ["code", "docs"],
                "confidence": report.get("brand", {}).get("confidence", "low"),
            }
        )
    # Content replacements – grouped summary per type
    for rtype, meta in report["occurrences"]["by_type"].items():
        actions["replace_content"].append(
            {
                "type": rtype,
                "variants": meta.get("values", []),
                "count": meta.get("count", 0),
                "impact": "medium" if rtype != "upper" else "high",
                "scope": ["code", "config", "docs"],
                "confidence": "medium",
            }
        )
    # Config updates from dynamic links / build info
    for link in report.get("dynamic_links", []):
        actions["update_config"].append(
            {
                "from": link.get("from"),
                "to": link.get("to"),
                "impact": "high",
                "scope": ["config"],
                "confidence": link.get("confidence", "low"),
            }
        )
    if report.get("build", {}).get("verify_command"):
        actions["update_config"].append(
            {
                "from": {"field": "build.verify_command"},
                "to": {"command": report["build"]["verify_command"]},
                "impact": "low",
                "scope": ["config"],
                "confidence": "high",
            }
        )
    report["actions"] = actions

    return report


def report_to_config(report: Dict, brand_new: str, package_new: str, cap_new_arg: str = "") -> Dict:
    """
    Convert analysis report to init_project config format.
    Priority: use discovered_replacements/discovered_file_renames if present;
    else fall back to brand/package/cap for backward compatibility.
    """
    bn = brand_new or report.get("brand", {}).get("old", "")
    pkg_new = package_new or report.get("package", {}).get("old", "")
    cap_new = cap_new_arg or (bn.capitalize() if bn else "")

    config = {
        "brand": {
            "old": report.get("brand", {}).get("old", ""),
            "new": bn,
        },
        "package": {
            "old": report.get("package", {}).get("old", ""),
            "new": pkg_new,
        },
        "project_root": ".",
        "directories": {"rename": []},
        "modules": {"remove": []},
        "preserve": {
            "patterns": report.get("preserve", {}).get("patterns", []),
            "paths": report.get("preserve", {}).get("paths", []),
        },
    }

    # Replacements: prefer discovered, else generate from brand/package/cap
    discovered = report.get("discovered_replacements", [])
    brand_old = report.get("brand", {}).get("old", "")
    if discovered:
        replacements = []

        def _segment_replace(s: str, old_seg: str, new_seg: str) -> str:
            """Replace brand segment (case-insensitive) in segment-separated identifiers."""
            if not old_seg or old_seg.lower() not in s.lower():
                return s
            idx = s.lower().find(old_seg.lower())
            return s[:idx] + new_seg + s[idx + len(old_seg):]

        def _is_path_style(ident: str) -> bool:
            """Path-style: has _/-/. as segment sep, and not PascalCase-only."""
            if not ident:
                return False
            if "_" in ident or "-" in ident or "." in ident:
                if ident.upper() == ident:
                    return False
                return True
            return ident.islower() or (ident[0].islower() if ident else False)

        for item in discovered:
            from_str = item.get("from", "")
            rtype = item.get("type", "brand")
            if rtype == "package":
                to_str = pkg_new
            elif rtype == "upper":
                to_str = _segment_replace(from_str, brand_old, bn.upper())
            elif rtype == "cap":
                if _is_path_style(from_str) and brand_old:
                    to_str = _segment_replace(from_str, brand_old, bn)
                elif brand_old and brand_old.lower() in from_str.lower():
                    idx = from_str.lower().find(brand_old.lower())
                    to_str = from_str[:idx] + cap_new + from_str[idx + len(brand_old):]
                elif brand_old and from_str.lower().startswith(brand_old.lower()) and len(from_str) > len(brand_old):
                    to_str = cap_new + from_str[len(brand_old):]
                else:
                    to_str = cap_new
            else:
                # brand type: replace brand segment in compound identifiers
                if brand_old and brand_old.lower() in from_str.lower() and len(from_str) > len(brand_old):
                    to_str = _segment_replace(from_str, brand_old, bn)
                else:
                    to_str = bn
            if from_str and from_str != to_str:
                replacements.append({"from": from_str, "to": to_str})
        # Sort by from length descending to avoid short-string-first replacement
        replacements.sort(key=lambda x: -len(x["from"]))
        config["replacements"] = replacements
    else:
        # Fallback: generate from brand/package/cap
        replacements = []
        pkg_old = report.get("package", {}).get("old", "")
        if pkg_old and pkg_new and pkg_old != pkg_new:
            replacements.append({"from": pkg_old, "to": pkg_new})
        cap_old = report.get("cap_old", "")
        if cap_old and cap_new and cap_old != cap_new:
            replacements.append({"from": cap_old, "to": cap_new})
        brand_old = report.get("brand", {}).get("old", "")
        if brand_old and bn and brand_old != bn:
            replacements.append({"from": brand_old, "to": bn})
        replacements.sort(key=lambda x: -len(x["from"]))
        config["replacements"] = replacements

    # File renames: prefer discovered, else empty
    discovered_fr = report.get("discovered_file_renames", [])
    if discovered_fr:
        config["file_renames"] = []
        for fr in discovered_fr:
            path = fr.get("path", "")
            new_name = fr.get("new_name", "").replace("{new_cap}", cap_new).replace("{new_brand}", bn)
            if path and new_name:
                config["file_renames"].append({"path": path, "new_name": new_name})
    else:
        config["file_renames"] = []

    # Cap (for backward compat with init that reads brand.cap_old)
    cap_old = report.get("cap_old", "")
    if cap_old:
        config["brand"]["cap_old"] = cap_old
        config["brand"]["cap_new"] = cap_new

    # Directories
    bn_val = config["brand"]["new"]
    for dr in report.get("directories", {}).get("rename", []):
        from_name = dr.get("from", "").replace("{new_brand}", bn_val)
        to_name = dr.get("to", "").replace("{new_brand}", bn_val)
        config["directories"]["rename"].append({"from": from_name, "to": to_name})

    # Build info
    build = report.get("build", {})
    if build:
        config["build"] = build

    return config


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Java project and generate init config draft"
    )
    parser.add_argument("--path", "-p", required=True, help="Project root path")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--format", "-f", choices=["yaml", "markdown", "both"], default="both")
    parser.add_argument("--brand-new", help="Proposed new brand (for config generation)")
    parser.add_argument("--package-new", help="Proposed new package (for config generation)")
    parser.add_argument("--cap-new", help="PascalCase form for cap_new, e.g. SuperRAG (when brand has acronyms)")
    parser.add_argument("--no-deep-scan", action="store_true", help="Skip full content scan, use existing inference only")

    args = parser.parse_args()
    project_root = Path(args.path).resolve()

    report = analyze(project_root, deep_scan=not args.no_deep_scan)
    if report.get("error"):
        print(f"Error: {report['error']}")
        return 1

    import yaml

    output_path = args.output
    if not output_path:
        output_path = str(project_root / "analyze-output")

    if args.brand_new or args.package_new:
        config = report_to_config(report, args.brand_new or "", args.package_new or "", args.cap_new or "")
        config["project_root"] = "."
        if args.format in ("yaml", "both"):
            out_yaml = output_path + ("" if output_path.endswith(".yaml") else "-config.yaml")
            with open(out_yaml, "w", encoding="utf-8") as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            print(f"Config draft written to: {out_yaml}")

    if args.format in ("yaml", "both"):
        report_file = output_path + ("" if output_path.endswith(".yaml") else "-report.yaml")
        with open(report_file, "w", encoding="utf-8") as f:
            yaml.dump(report, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"Analysis report written to: {report_file}")

    if args.format in ("markdown", "both"):
        md_file = output_path + ("" if output_path.endswith(".md") else "-checklist.md")
        config_preview = report_to_config(report, args.brand_new or "", args.package_new or "", args.cap_new or "") if (args.brand_new or args.package_new) else {}
        with open(md_file, "w", encoding="utf-8") as f:
            f.write("# 项目分析修改清单\n\n")
            f.write(f"**项目路径**: `{report['project_root']}`\n\n")
            f.write("## 推断结果\n\n")
            f.write(f"- **package.old**: `{report.get('package', {}).get('old', '')}` "
                   f"（置信度: {report.get('package', {}).get('confidence', '')}）\n")
            f.write(f"- **brand.old**: `{report.get('brand', {}).get('old', '')}` "
                   f"（置信度: {report.get('brand', {}).get('confidence', '')}）\n")
            f.write(f"- **cap_old 建议**: `{report.get('cap_old', '')}`\n")
            f.write(f"- **cap_new** (PascalCase): 若品牌含缩写（如 SuperRAG），请用 `--cap-new SuperRAG` 或编辑 config 中 `brand.cap_new` 后执行\n\n")
            f.write("## 需人工确认\n\n")
            for item in report.get("needs_review", []):
                f.write(f"- {item}\n")
            f.write("\n## 确认前自检（请逐项核对）\n\n")
            f.write("- [ ] `cap_new` 是否符合 PascalCase 预期（含缩写如 SuperRAG 时请修改 config）\n")
            f.write("- [ ] `package.new` 是否满足当前生态的包/模块命名规范\n")
            f.write("- [ ] 是否需添加 `preserve.patterns`（如第三方 groupId、域名、Storage Key 前缀）\n")
            f.write("- [ ] 是否需调整 `project_name_new`（项目显示名：pyproject/package.json/pom name）\n\n")
            f.write("## 内容替换 (replacements)\n\n")
            for r in config_preview.get("replacements", [])[:30]:
                f.write(f"- `{r.get('from')}` -> `{r.get('to')}`\n")
            if len(config_preview.get("replacements", [])) > 30:
                f.write(f"- ... 共 {len(config_preview['replacements'])} 项\n")
            f.write("\n## 文件重命名 (file_renames)\n\n")
            for fr in config_preview.get("file_renames", [])[:20]:
                f.write(f"- `{fr.get('path')}` -> `{fr.get('new_name')}`\n")
            if len(config_preview.get("file_renames", [])) > 20:
                f.write(f"- ... 共 {len(config_preview['file_renames'])} 项\n")
            f.write("\n## 目录重命名\n\n")
            for dr in report.get("directories", {}).get("rename", [])[:20]:
                f.write(f"- `{dr.get('from')}` -> `{dr.get('to')}`\n")
            if len(report.get("directories", {}).get("rename", [])) > 20:
                f.write(f"- ... 共 {len(report['directories']['rename'])} 项\n")
            build = report.get("build", {})
            if build.get("verify_command"):
                f.write("\n## 建议验证命令\n\n")
                f.write(f"```bash\n{build['verify_command']}\n```\n\n")
            f.write("## 文件类型分布\n\n")
            for ext, cnt in sorted(report.get("file_types", {}).items(), key=lambda x: -x[1]):
                f.write(f"- `*{ext}`: {cnt} 个文件\n")
        print(f"Checklist written to: {md_file}")

    return 0


if __name__ == "__main__":
    exit(main())
