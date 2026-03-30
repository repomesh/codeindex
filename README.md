# Repo Viz Explorer

An interactive visualization tool for exploring Python repository structure. Point it at any Python project and get live, multi-mode dependency graphs rendered in your browser — no build step, no external dependencies beyond the stdlib.

![Visualization modes: 2D force graph, 3D network, dependency matrix, treemap](https://img.shields.io/badge/views-4%20modes-00d4ff?style=flat-square) ![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square) ![Zero dependencies](https://img.shields.io/badge/deps-stdlib%20only-10b981?style=flat-square)

---

## Features

- **4 visualization modes** — 2D force-directed graph, 3D network, dependency matrix, and treemap
- **Live AST analysis** — parses your actual `.py` files using Python's built-in `ast` module; no third-party tools needed
- **Search & filter** — type to highlight a module and its neighbors, dimming everything else
- **Node detail panel** — click any node to see full path, LOC, what it imports, and what imports it
- **Cycle detection** — circular import pairs highlighted in red automatically
- **Cluster mode** — group nodes by directory in the force graph
- **Sort & zoom** — matrix sorts by name/connections/LOC; treemap drills into groups with breadcrumb navigation
- **Export** — download the 2D graph as SVG or the 3D view as PNG
- **Auto-refresh** — `--watch` mode re-analyzes on every `.py` file change
- **Keyboard shortcuts** — `1`–`4` switch tabs, `F` focuses search, `R` refreshes

---

## Quickstart

```bash
git clone <this-repo>
cd repo-viz-explorer

# Analyze a Python project and serve the UI
python server.py --repo /path/to/your/python/project

# Open in browser
open http://localhost:8080
```

That's it. No `pip install`, no npm, no build step.

---

## Usage

### `server.py`

```
python server.py [--repo PATH] [--port PORT] [--watch]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--repo` | `.` | Path to the Python project to analyze |
| `--port` | `8080` | Port to serve on |
| `--watch` | off | Auto-re-analyze when `.py` files change (requires `watchdog`) |

You can also set the repo path via environment variable:

```bash
REPO_PATH=./myapp python server.py
```

**With file watching:**

```bash
pip install watchdog
python server.py --repo ./myapp --watch
```

### `analyze_repo.py`

Run the analyzer standalone to produce `repo_graph.json` without starting the server:

```bash
python analyze_repo.py ./myapp
# → writes repo_graph.json in the current directory

python analyze_repo.py ./myapp --output /tmp/graph.json
```

---

## Output format

`analyze_repo.py` emits a single JSON file:

```json
{
  "meta": {
    "root": "myapp/",
    "total_files": 12,
    "total_loc": 3400
  },
  "nodes": [
    { "id": "app.py", "type": "module", "size": 420, "loc": 420, "group": 0, "imports": 5 }
  ],
  "links": [
    { "source": "app.py", "target": "api/routes.py", "weight": 2 }
  ]
}
```

**Node types:**

| Type | Color | Meaning |
|------|-------|---------|
| `module` | cyan | A `.py` file |
| `config` | red | A `.py` file named `config`, `settings`, `constants`, or `env` |
| `import` | amber | An external library (not in the repo) |
| `class` | purple | A top-level class definition |
| `function` | green | A top-level function definition |

**Edge weight** = number of import references between source and target.
**Group** = integer directory cluster ID (same directory → same group).

---

## Visualization modes

### 2D Force Graph
Force-directed layout using D3. Drag nodes, scroll to zoom. Edges are colored by type: **cyan** for internal imports, **amber** for external libraries, **red** for circular imports.

Controls:
- Search bar — type to highlight matching modules and their neighbors
- **CLUSTER** toggle — pulls nodes toward their directory centroid
- Click a node — opens detail panel with full import/imported-by lists
- **↓ SVG** — exports current view as an SVG file

### 3D Network
Three.js sphere layout, nodes grouped by directory with a color legend. Drag to orbit, scroll to zoom, right-drag to pan. Click a node to see its details in the sidebar.

Controls:
- **↓ PNG** — exports current canvas as a PNG

### Dependency Matrix
Grid showing import relationships between all modules. Cell intensity encodes weight; diagonal cells (self-references, which indicate a bug) are highlighted.

Controls:
- **Sort by** — name, most connections, or most LOC
- Hover a cell — highlights the entire row and column

### Treemap
Area-proportional view of the repo structure.

Controls:
- **Size by** — LOC or connection count
- Click a group rectangle — zooms into that directory
- Breadcrumb trail — click any segment to navigate back up

---

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| `1` – `4` | Switch to tab 1–4 |
| `F` | Focus the search bar |
| `R` | Refresh graph data |
| `Esc` | Clear search / selection |

---

## Architecture

```
repo-viz-explorer/
├── repo-viz-explorer.html   # Single-file frontend (D3 + Three.js, no build step)
├── analyze_repo.py          # AST walker → repo_graph.json (stdlib only)
├── server.py                # HTTP server: serves UI + graph + /refresh (stdlib only)
└── repo_graph.json          # Generated output (gitignore this if you prefer)
```

- **Frontend** — single HTML file with all CSS and JS inlined. D3 v7 and Three.js r128 loaded from cdnjs CDN.
- **Backend** — pure Python stdlib (`http.server`, `ast`, `pathlib`, `json`). No Flask, FastAPI, or any third-party packages required.
- **Optional** — `watchdog` for `--watch` mode is the only allowed third-party dependency.

---

## Offline / static use

The HTML file works standalone with sample data — just open it directly in a browser:

```bash
open repo-viz-explorer.html
```

It will silently fall back to hardcoded sample data if `/graph` is unreachable.

---

## Requirements

- Python 3.8+
- A modern browser (Chrome, Firefox, Safari, Edge)
- Internet access for CDN fonts and libraries (D3, Three.js) — or swap the CDN links for local copies

---

## License

MIT
