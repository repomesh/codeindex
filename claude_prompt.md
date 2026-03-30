# Task: Iterate on Repo Visualization Explorer

I'm attaching `repo-viz-explorer.html` — a single-file interactive visualization tool for exploring Python repository structure. It currently demonstrates 4 visualization modes using hardcoded sample data.

## Your Mission

Evolve this into a **real, functional repo analyzer** that can parse an actual Python project and render live visualizations. Work iteratively, committing progress at each stage.

---

## Phase 1 — Python AST Parser (Backend)

Create `analyze_repo.py` that:

- Accepts a repo root path as a CLI argument: `python analyze_repo.py ./myapp`
- Walks all `.py` files recursively (respecting `.gitignore` if present)
- Uses Python's built-in `ast` module to extract:
  - Module nodes (each `.py` file)
  - `import` and `from X import Y` statements → edges
  - Top-level `class` definitions → class nodes
  - Top-level `def` definitions → function nodes
  - External vs. internal imports (internal = exists in the repo)
- Counts lines of code (LOC) per file
- Outputs a single `repo_graph.json` with this exact shape:
```json
{
  "meta": { "root": "myapp/", "total_files": 12, "total_loc": 3400 },
  "nodes": [
    { "id": "app.py", "type": "module", "size": 420, "loc": 420, "group": 0, "imports": 5 }
  ],
  "links": [
    { "source": "app.py", "target": "api/routes.py", "weight": 2 }
  ]
}
```

- `type` is one of: `"module"`, `"class"`, `"function"`, `"import"` (external), `"config"`
- `weight` = number of import references between source and target
- `group` = integer cluster ID (assign by directory)
- Config files: any `.py` file named `config`, `settings`, `constants`, or `env`

---

## Phase 2 — Serve & Load Live Data

Create a minimal `server.py` using Python's built-in `http.server`:

- Serves `repo-viz-explorer.html` at `/`
- Serves `repo_graph.json` at `/graph`
- Accepts a `?repo=./path/to/project` query param on startup (or env var `REPO_PATH`)
- Auto-runs `analyze_repo.py` on startup to regenerate `repo_graph.json`
- Adds a `/refresh` endpoint that re-runs analysis and returns `{ "ok": true }`

Update `repo-viz-explorer.html` to:

- On load, `fetch('/graph')` and replace the hardcoded `NODES`/`LINKS` constants
- Show a loading state while fetching
- Add a **⟳ Refresh** button in the header that calls `/refresh` then reloads data
- Display real `meta` values (file count, LOC) in the sidebar stats

---

## Phase 3 — Visualization Enhancements

With real data now flowing, improve each view:

**2D Force Graph:**
- Add a **search/filter bar** — type a module name to highlight it and its direct neighbors, dimming all others
- On node click, show a persistent side panel with: full path, LOC, list of what it imports, list of what imports it
- Color edges by type: internal imports (cyan), external library imports (amber)
- Add a **cluster mode** toggle that uses `d3.forceCluster` to group nodes by directory

**3D Network:**
- Color nodes by directory group with a legend
- Add node labels that billboard toward the camera
- On click, log node info to the sidebar panel

**Dependency Matrix:**
- Highlight entire row+column on hover
- Add a sort control: sort by name, by most connections, or by LOC
- Color diagonal cells differently (self-reference = bug indicator)

**Treemap:**
- Click a group rectangle to zoom into it
- Show a breadcrumb trail for navigation
- Add a toggle: size by LOC vs. size by connection count

---

## Phase 4 — Polish

- Add a `--watch` flag to `server.py` that uses `watchdog` to auto-refresh `repo_graph.json` when `.py` files change
- Add cycle detection: highlight any circular import pairs in red in the 2D graph
- Export buttons: download current view as SVG (2D) or PNG (3D)
- Keyboard shortcuts: `1`–`4` to switch tabs, `F` to focus search, `R` to refresh
- Make the UI responsive down to 1024px wide

---

## Constraints

- Single HTML file for the frontend (inline all JS/CSS — no build step)
- Backend is pure Python stdlib only for `server.py` (no Flask, FastAPI, etc.)
- `analyze_repo.py` may use stdlib only (`ast`, `os`, `pathlib`, `json`, `re`)
- `watchdog` (Phase 4 only) is the one allowed third-party dependency
- All D3 and Three.js loaded from cdnjs CDN links already in the HTML
- Preserve the existing dark terminal aesthetic — extend it, don't replace it

---

## Files I'm Providing

- `repo-viz-explorer.html` — the current visualization frontend

## Deliverables Per Phase

After each phase, confirm what was built, any assumptions made, and what to run. Target invocation when done:
```bash
python server.py --repo ./myapp
# → opens http://localhost:8080
```