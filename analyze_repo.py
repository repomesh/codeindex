#!/usr/bin/env python3
"""
analyze_repo.py — AST-based Python repo analyzer.
Usage: python analyze_repo.py ./myapp [--output repo_graph.json]
"""
import ast
import json
import os
import re
import sys
from pathlib import Path

CONFIG_NAMES = {"config", "settings", "constants", "env", "configuration", "conf"}
STDLIB_TOP = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else set()


def load_gitignore_patterns(root):
    gi = root / ".gitignore"
    patterns = []
    if gi.exists():
        for line in gi.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Convert glob to regex (simple)
            pat = re.escape(line).replace(r"\*\*", ".*").replace(r"\*", "[^/]*").replace(r"\?", ".")
            patterns.append(re.compile(pat))
    return patterns


def is_ignored(path, root, patterns):
    rel = str(path.relative_to(root))
    for pat in patterns:
        if pat.search(rel):
            return True
    return False


def collect_py_files(root):
    patterns = load_gitignore_patterns(root)
    files = []
    for p in sorted(root.rglob("*.py")):
        if any(part.startswith(".") or part in {"__pycache__", "node_modules", ".venv", "venv", "env", ".git"}
               for part in p.parts):
            continue
        if is_ignored(p, root, patterns):
            continue
        files.append(p)
    return files


def dir_group(path, root, group_map):
    rel = path.relative_to(root)
    key = str(rel.parent) if str(rel.parent) != "." else ""
    if key not in group_map:
        group_map[key] = len(group_map)
    return group_map[key]


def node_type(path):
    stem = path.stem.lower()
    if stem in CONFIG_NAMES:
        return "config"
    return "module"


def parse_imports(tree):
    """Return list of (kind, module_name) where kind is 'import' or 'from'."""
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(("import", alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(("from", node.module))
    return imports


def resolve_internal(mod_name, file_path, root, all_files):
    """Try to map a module name to a relative .py path in the repo."""
    parts = mod_name.split(".")
    # Direct match: foo.bar -> foo/bar.py or foo/bar/__init__.py
    candidates = [
        "/".join(parts) + ".py",
        "/".join(parts) + "/__init__.py",
    ]
    for c in candidates:
        if c in all_files:
            return c
    # Relative from file's dir
    rel_base = str(file_path.parent.relative_to(root))
    if rel_base != ".":
        for c in candidates:
            full = f"{rel_base}/{c}"
            if full in all_files:
                return full
    return None


def analyze(root_path: str) -> dict:
    root = Path(root_path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Path not found: {root}")

    py_files = collect_py_files(root)
    group_map: dict[str, int] = {}
    all_rel: set[str] = set()
    for f in py_files:
        all_rel.add(str(f.relative_to(root)))

    nodes = []
    links_map: dict[tuple[str, str], int] = {}
    external_nodes: dict[str, dict] = {}
    total_loc = 0

    for f in py_files:
        rel = str(f.relative_to(root))
        try:
            source = f.read_text(errors="replace")
        except OSError:
            continue

        loc = source.count("\n") + 1
        total_loc += loc

        try:
            tree = ast.parse(source, filename=str(f))
        except SyntaxError:
            tree = None

        imports_list = parse_imports(tree) if tree else []
        import_count = len(imports_list)

        ntype = node_type(f)
        group = dir_group(f, root, group_map)

        nodes.append({
            "id": rel,
            "type": ntype,
            "size": loc,
            "loc": loc,
            "group": group,
            "imports": import_count,
        })

        for _kind, mod in imports_list:
            top_level = mod.split(".")[0]
            internal = resolve_internal(mod, f, root, all_rel)
            if internal:
                key = (rel, internal)
                links_map[key] = links_map.get(key, 0) + 1
            else:
                # External import node
                if top_level not in external_nodes:
                    external_nodes[top_level] = {
                        "id": top_level,
                        "type": "import",
                        "size": 40,
                        "loc": 0,
                        "group": len(group_map) + 100,
                        "imports": 0,
                    }
                key = (rel, top_level)
                links_map[key] = links_map.get(key, 0) + 1

    # Add external nodes
    nodes.extend(external_nodes.values())

    links = [{"source": s, "target": t, "weight": w} for (s, t), w in links_map.items()]

    return {
        "meta": {
            "root": str(root.name) + "/",
            "total_files": len(py_files),
            "total_loc": total_loc,
        },
        "nodes": nodes,
        "links": links,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Analyze a Python repo and emit repo_graph.json")
    parser.add_argument("repo", help="Path to repo root")
    parser.add_argument("--output", default="repo_graph.json", help="Output JSON file")
    args = parser.parse_args()

    print(f"Analyzing {args.repo} …", file=sys.stderr)
    data = analyze(args.repo)
    out = Path(args.output)
    out.write_text(json.dumps(data, indent=2))
    meta = data["meta"]
    print(f"Done. {meta['total_files']} files, {meta['total_loc']} LOC → {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
