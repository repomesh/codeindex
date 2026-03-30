#!/usr/bin/env python3
"""
analyze_repo.py — Multi-language repo analyzer (dispatcher).
Detects languages present in a repo and delegates to per-language plugins.

Usage: python analyze_repo.py ./myapp [--output repo_graph.json]
"""
import json
import sys
from pathlib import Path

# Ensure the project root is on sys.path so `analyzers` package is importable
sys.path.insert(0, str(Path(__file__).parent))
from analyzers import python_analyzer, js_analyzer, css_analyzer

_SKIP = {"__pycache__", ".venv", "venv", "env", ".git", "node_modules", "dist", "build", ".next"}


def detect_languages(root: Path):
    """Return a list of language identifiers found in the repo."""
    langs = []

    # Python: any .py file outside skip dirs
    if any(
        p for p in root.rglob("*.py")
        if not any(part in _SKIP for part in p.parts)
    ):
        langs.append("python")

    # JavaScript / TypeScript / Vue
    js_signals = ["*.js", "*.ts", "*.jsx", "*.tsx", "*.mjs", "*.vue"]
    if (root / "package.json").exists() or any(
        p for sig in js_signals
        for p in root.rglob(sig)
        if not any(part in _SKIP for part in p.parts)
    ):
        langs.append("javascript")

    # CSS / SCSS / Less
    css_signals = ["*.css", "*.scss", "*.sass", "*.less", "*.styl"]
    if any(
        p for sig in css_signals
        for p in root.rglob(sig)
        if not any(part in _SKIP for part in p.parts)
    ):
        langs.append("css")

    return langs


def merge_links(target: dict, source: dict) -> None:
    for k, v in source.items():
        target[k] = target.get(k, 0) + v


def link_kind(s_type: str, t_type: str) -> str:
    """Determine the semantic kind of a dependency edge."""
    if s_type == "style" or t_type == "style":
        return "styles"
    if s_type in {"component", "route"} and t_type in {"component", "route"}:
        return "renders"
    return "imports"


def analyze(root_path: str) -> dict:
    root = Path(root_path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Path not found: {root}")

    langs = detect_languages(root)
    if not langs:
        print(f"Warning: no supported languages detected in {root}", file=sys.stderr)

    group_map = {}
    all_nodes = []
    all_links_map = {}
    external_seen = set()
    total_files = 0
    total_loc = 0
    meta_extra = {}

    def add_results(nodes, ext_nodes, links_map, meta):
        nonlocal total_files, total_loc
        all_nodes.extend(nodes)
        for en in ext_nodes:
            if en["id"] not in external_seen:
                all_nodes.append(en)
                external_seen.add(en["id"])
        merge_links(all_links_map, links_map)
        total_files += meta.get("total_files", 0)
        total_loc += meta.get("total_loc", 0)

    if "python" in langs:
        nodes, ext_nodes, links_map, meta = python_analyzer.analyze(root, group_map)
        add_results(nodes, ext_nodes, links_map, meta)

    if "javascript" in langs:
        nodes, ext_nodes, links_map, meta = js_analyzer.analyze(root, group_map)
        add_results(nodes, ext_nodes, links_map, meta)
        for key in ("framework", "packageManager"):
            if meta.get(key):
                meta_extra[key] = meta[key]

    if "css" in langs:
        nodes, ext_nodes, links_map, meta = css_analyzer.analyze(root, group_map)
        add_results(nodes, ext_nodes, links_map, meta)

    # Build links with semantic kind annotation
    node_type_map = {n["id"]: n.get("type", "module") for n in all_nodes}
    links = []
    for (s, t), w in all_links_map.items():
        kind = link_kind(node_type_map.get(s, "module"), node_type_map.get(t, "module"))
        links.append({"source": s, "target": t, "weight": w, "kind": kind})

    return {
        "meta": {
            "root": str(root.name) + "/",
            "total_files": total_files,
            "total_loc": total_loc,
            "languages": langs,
            **meta_extra,
        },
        "nodes": all_nodes,
        "links": links,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Analyze a repo and emit repo_graph.json")
    parser.add_argument("repo", help="Path to repo root")
    parser.add_argument("--output", default="repo_graph.json", help="Output JSON file")
    args = parser.parse_args()

    print(f"Analyzing {args.repo} …", file=sys.stderr)
    data = analyze(args.repo)
    out = Path(args.output)
    out.write_text(json.dumps(data, indent=2))
    meta = data["meta"]
    langs_str = ", ".join(meta.get("languages", ["unknown"]))
    print(
        f"Done. {meta['total_files']} files, {meta['total_loc']} LOC "
        f"[{langs_str}] → {out}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
