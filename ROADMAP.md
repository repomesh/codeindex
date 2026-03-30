# Repo Visualizer — Multi-Language Expansion Roadmap

## Overview

The visualizer currently supports Python repositories (AST-based analysis, import graph, dependency matrix, treemap, 3D network). This roadmap expands it to support web technologies and other languages in logical phases.

The core extension point is `analyze_repo.py`, which produces a language-agnostic JSON schema (`{ nodes[], links[], meta }`) that the frontend already consumes.

---

## Phase 1 — JavaScript / TypeScript ✅ COMPLETE

**Goal:** Support JS/TS repos with the same visualizations Python already gets.

### Tasks
- [x] Refactor `analyze_repo.py` into a dispatcher + plugin architecture (`analyzers/` directory)
- [x] Create `analyzers/python_analyzer.py` (extract existing Python logic)
- [x] Create `analyzers/js_analyzer.py`:
  - Detect `.js`, `.ts`, `.jsx`, `.tsx` files
  - Parse `import X from 'Y'` and `require('Y')` with regex
  - Read `package.json` to distinguish internal vs. external deps
  - Detect framework from `package.json` dependencies (React, Vue, Next, Nuxt, Angular, Svelte)
- [x] Auto-detect which language(s) are present in a repo
- [x] Extend JSON schema:
  - `node.language: "python" | "javascript" | "typescript"`
  - `node.framework: "react" | "vue" | "next" | null`
  - `meta.packageManager: "npm" | "yarn" | "pnpm" | null`
  - `meta.languages: string[]`
- [x] Update frontend (`repo-viz-explorer.html`):
  - Language badge on node detail panel
  - Language-aware node colors (cyan = Python, yellow = JS, blue = TS)
  - Language filter toggle in sidebar
  - Show framework in meta stats bar

### Success Criteria
- Run `python server.py --repo ./some-react-app` and see a full dependency graph
- Nodes colored by language, external npm packages shown as `import` type nodes
- Framework detected and shown in stats

---

## Phase 2 — Frontend Framework Depth ✅ COMPLETE

**Goal:** Go beyond file-level imports to understand component/route/hook structure.

### Tasks
- [x] React: detect components (JSX files / JSX-returning .js), hooks (`use*` naming), context/store providers
- [x] Vue: parse `.vue` SFCs — extract `<script>` imports, classify as component
- [x] CSS/SCSS/Less: new `css_analyzer.py` — parse `@import`, `@use`, `@forward` as dependency edges
- [x] Route detection: `pages/`, `routes/`, `views/`, `screens/` dirs + Next.js app router filenames
- [x] Extend schema:
  - `node.type: "component" | "hook" | "route" | "store" | "style"`
  - `link.kind: "imports" | "renders" | "styles"`
- [x] Frontend: distinct colors per node type (pink=component, green=hook, orange=route, purple=store, teal=style)
- [x] Link edges colored by kind (pink=renders, teal=styles, cyan=imports)
- [x] Matrix view includes all internal node types
- [x] Language legend updated with vue/css/scss/less

### Success Criteria
- ✅ React components (pink), routes (orange), hooks (green), stores (purple) visually distinct
- ✅ Vue SFCs detected as components, imports extracted from `<script>` block
- ✅ CSS/SCSS files tracked with `@import` dependency edges
- ✅ "renders" edges (pink) visible between components in the force graph

---

## Phase 3 — Multi-language Backend Support

**Goal:** Support common server-side languages using the same plugin pattern from Phase 1.

### Tasks
- [ ] `analyzers/go_analyzer.py` — `.go` files, `go.mod` for deps, `import "pkg/path"` parsing
- [ ] `analyzers/ruby_analyzer.py` — `.rb` files, `Gemfile`, `require 'file'` parsing
- [ ] `analyzers/rust_analyzer.py` — `.rs` files, `Cargo.toml`, `use crate::module` parsing
- [ ] `analyzers/java_analyzer.py` — `.java`/`.kt` files, `pom.xml`/`build.gradle`, `import com.pkg.Class`
- [ ] `analyzers/php_analyzer.py` — `.php` files, `composer.json`, `require`/`use` parsing
- [ ] Update dispatcher to detect and run all relevant analyzers for a repo
- [ ] Update frontend colors and language filter for new languages

### Language Detection Heuristics
| Signal | Language |
|--------|----------|
| `go.mod` present | Go |
| `Gemfile` present | Ruby |
| `Cargo.toml` present | Rust |
| `pom.xml` or `build.gradle` | Java/Kotlin |
| `composer.json` present | PHP |

### Success Criteria
- A Go repo produces a full module dependency graph
- A Ruby Rails app shows controller/model/view relationships

---

## Phase 4 — Infrastructure & Config Layer

**Goal:** Visualize the operational glue — services, pipelines, environments.

### Tasks
- [ ] `analyzers/docker_analyzer.py` — parse `Dockerfile` and `docker-compose.yml` → service dependency graph
- [ ] `analyzers/ci_analyzer.py` — parse GitHub Actions (`.github/workflows/`) and GitLab CI (`.gitlab-ci.yml`) → pipeline stage visualization
- [ ] `analyzers/schema_analyzer.py` — parse `schema.sql`, Prisma schemas, SQLAlchemy models → entity-relationship view
- [ ] `.env` file analysis — identify config/secret references across code
- [ ] New frontend tab: "Infrastructure View" (services, not files)
- [ ] New node types: `service`, `pipeline-stage`, `database-table`, `env-var`

### Success Criteria
- Docker Compose multi-service app shows service dependency graph
- CI/CD pipeline stages shown as a flow diagram

---

## Phase 5 — Monorepo & Cross-language Intelligence

**Goal:** Handle complex projects with multiple languages, unified into one visualization.

### Tasks
- [ ] Single-pass language detection across entire repo
- [ ] Merge graphs from multiple analyzers into one unified visualization
- [ ] Cross-language boundary detection (e.g., Python API endpoint called by JS fetch)
- [ ] Workspace/monorepo support:
  - `pnpm workspaces`
  - `nx.json` / Turborepo
  - Poetry monorepos
  - Lerna
- [ ] UI layer/language filtering: show only frontend, only backend, only infra, or all
- [ ] "Package map" view: visualize packages/workspaces as first-class nodes

### Success Criteria
- A full-stack monorepo (Python API + React frontend) shows both sides in one graph
- Can filter to see only the frontend or only the backend subgraph

---

## Architecture Reference

### Current Structure
```
analyze_repo.py          ← monolithic Python-only analyzer
server.py                ← HTTP server (no changes needed per phase)
repo-viz-explorer.html   ← frontend (extend per phase)
repo_graph.json          ← output (schema is already language-agnostic)
```

### Target Structure (after Phase 1)
```
analyze_repo.py          ← dispatcher: detects languages, delegates to plugins
analyzers/
  __init__.py
  base.py                ← BaseAnalyzer ABC with shared helpers
  python_analyzer.py     ← extracted from original analyze_repo.py
  js_analyzer.py         ← new in Phase 1
server.py                ← unchanged
repo-viz-explorer.html   ← extended per phase
repo_graph.json          ← unchanged schema, extended fields
```

### JSON Schema (extended)
```json
{
  "meta": {
    "root": "myapp/",
    "total_files": 102,
    "total_loc": 24792,
    "languages": ["python", "javascript"],
    "packageManager": "npm"
  },
  "nodes": [
    {
      "id": "src/App.tsx",
      "type": "module",
      "language": "typescript",
      "framework": "react",
      "size": 142,
      "loc": 142,
      "group": 1,
      "imports": 5
    }
  ],
  "links": [
    {
      "source": "src/App.tsx",
      "target": "src/components/Header.tsx",
      "weight": 1,
      "kind": "imports"
    }
  ]
}
```
