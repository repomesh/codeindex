# Changelog

All notable changes to this project will be documented in this file.

## [0.3.2] - 2026-06-07

### Fixed

- **TypeScript path alias resolution** — imports using `@/*`, `~/`, or any
  alias defined in `tsconfig.json` / `jsconfig.json` `compilerOptions.paths`
  were silently treated as external packages. All reverse-dependency counts,
  blast scores, and `imported_by` lists were therefore zero for every real
  source file in TypeScript repos. The JS analyzer now reads path aliases and
  resolves them to actual file paths before falling back to the external-package
  path.
- **History backfill `first_seen_commit` overwrites** — `apply_file_temporal`
  and `apply_edge_temporal` guarded updates with `WHERE first_seen_commit IS
  NULL`. Because `analyze()` always writes the current HEAD commit as
  `first_seen_commit` on insert, the NULL guard silently suppressed every
  history update. Both methods now unconditionally overwrite with the
  historically-derived value. `apply_edge_temporal` also drops the `kind=`
  filter so `renders`/`styles`/`depends` edges are updated alongside `imports`
  edges.
- **`changed-since` modified files** — output now includes a `Modified files`
  section (files with content changes but no structural add/remove) derived
  from `git diff --name-status`. Added `git_modified()` to `index.py`.
- **`changed-since` edge noise** — added/removed edges are now filtered to
  only those where source or target is a touched file (modified, added, or
  removed). Previously the entire accumulated graph diff was emitted.
  Suppressed edge count is reported so nothing is silently hidden; `--json`
  still returns the full set.
- **Non-source nodes in outputs** — `high-blast` and `changed-since` now
  exclude `service`, `pipeline`, `database`, and `import` node types (Docker
  services, CI pipelines, npm packages) from all file and edge output.
- **FTS prefix search for natural-language queries** — `fts_search` now builds
  `word1* OR word2* OR ...` as the primary query so `auth login` also matches
  `authenticate`, `loginAction`, etc. Special FTS5 syntax characters are
  stripped before query construction to prevent `OperationalError`.
- **Graph expansion noise in search ranking** — `graph_expand` is now skipped
  when FTS (or semantic KNN) already returns ≥ k results, preventing
  structurally adjacent but semantically unrelated symbols from diluting
  high-quality keyword hits.
- **Search file aggregation** — `codeindex search` and the `semantic_search`
  MCP tool now include a `Files` section aggregating results by file (sorted
  by symbol hit count). The entry-point file appears even when no single
  symbol from it ranks at the top.
- **`db status` FTS row count** — `codeindex db status` now shows
  `fts_symbols` (rows in `symbols_fts`) making it easy to diagnose whether
  the FTS index is populated.

## [0.3.1] - 2026-06-07

### Fixed

- **Multi-word FTS search OR fallback** — `codeindex search "auth token"` previously
  returned nothing when AND semantics found no single symbol containing all words.
  `fts_search()` now retries with `word1 OR word2 OR ...` automatically when the
  AND query returns zero results.
- **`changed-since` backfill warning** — when `codeindex history` has never been run,
  all files share exactly one `first_seen_commit`, making `changed-since` results
  inaccurate against any older ref. The command now detects this via
  `COUNT(DISTINCT first_seen_commit) <= 1` and prints a clear warning on stderr
  (CLI) / includes a `"warning"` key in the response (JSON + MCP tool) directing
  the user to run `codeindex history` first.

## [0.3.0] - 2026-06-07

### Summary

codeindex evolves from a stateless point-in-time dependency analyzer into a
**temporal code knowledge graph** — persistent, incremental, and semantically
queryable. Three new properties: persistence + incrementality, time, and
meaning (semantic retrieval). All existing CLI commands, JSON schemas, and MCP
tools are unchanged.

### Added

#### Persistent SQLite store (Phase 1)
- `.codeindex/index.db` — SQLite graph store created automatically on
  `codeindex analyze`; survives across runs, never touches `codeindex.json`
- Incremental indexing: detects changed files via `git diff --name-status`
  between index runs; logs changed file count to stderr
- `codeindex db status` — schema version, last indexed commit, file/edge/symbol counts
- `codeindex db migrate` — applies pending schema migrations (runs automatically on open)
- `codeindex symbols` now syncs symbols to DB with FTS5 full-text index

#### Temporal layer (Phase 2)
- Every file, edge, and symbol carries `first_seen_commit` / `last_seen_commit`
  — facts are never hard-deleted, only soft-deleted with temporal stamps
- `codeindex history [--since REF] [--max-commits N]` — backfills temporal
  data from git history without any working-tree checkouts (uses
  `git ls-tree` + `git cat-file --batch`)
- `codeindex changed-since <ref>` — files and edges added or removed since a
  commit, branch, or tag
- `codeindex impact <file> --as-of <ref>` — blast radius at a historical point
  in time, not just HEAD

#### Semantic layer (Phase 3)
- `codeindex search "<query>" [--k N] [--as-of REF] [--json]` — hybrid
  semantic + FTS5 keyword + graph expansion search, fused with Reciprocal Rank
  Fusion (RRF)
- `codeindex/semantic/provider.py` — `EmbeddingProvider` ABC +
  `OpenAIEmbeddingProvider` HTTP client (stdlib `urllib` only, no new runtime deps)
- `sqlite-vec` optional extension for KNN vector search; absent = graceful
  fallback to FTS + graph with a clear notice (no crash, no config required)
- Embeddings generated automatically during `codeindex analyze` when
  `CODEINDEX_EMBEDDING_ENDPOINT` / `_MODEL` / `_DIMS` env vars are set
- `codeindex[semantic]` extra: `pip install 'codeindex[semantic]'`

#### MCP surface (Phase 4) — 4 new tools, existing 6 unchanged
- `semantic_search` — hybrid search from an MCP client; degrades gracefully
- `temporal_impact` — blast radius at a historical `as_of` ref
- `graph_query` — k-hop dependency neighborhood (`dependents` / `dependencies` / `both`)
- `changed_since` — files and edges added or removed since a ref

### Changed
- `schema_version` bumped to `"2"` with forward migration from `"1"`
- FTS5 `symbols_fts` rowid now equals `symbols.id` (enables direct FTS → symbol
  row mapping without a secondary lookup)
- `codeindex db status` output extended with `embedding_model`, `embedding_dims`,
  `vec_symbols` fields
- README rewritten to document all new commands, the SQLite store, semantic
  setup, and the full 10-tool MCP surface

### Internal
- `codeindex/store/db.py`: `Store` class — `init_vectors()`, `upsert_embeddings()`,
  `semantic_search()`, `fts_search()`, `graph_expand()`, `neighborhood()`,
  `symbol_visible_at()`, `get_symbol()`, `symbols_needing_embeddings()`
- `codeindex/temporal/history.py`: `backfill()` — BFS over git log via plumbing
  commands; no checkout side-effects
- `codeindex/semantic/search.py`: `hybrid_search()` with RRF fusion
- Dependency direction enforced: `store/` and `temporal/` never import from
  `semantic/` or `graph/`
- 7 new Phase 3 tests; 6 Phase 2 tests; 5 Phase 1 tests (18 total, all green)

## [0.2.0] - 2026-05-24

### Added
- `codeindex lookup <symbol>` — find where a symbol is defined (file + line)
- `codeindex dependencies <file>` — show imports and imported-by for a file
- `codeindex high-blast` — list files above a blast score threshold
- All three new commands support `--json` for machine-readable output
- `lookup_symbol` and `build_symbol_index` tools in MCP server
- CLI integration test suite (`benchmark/test_cli.py`) — 37 assertions covering happy path, `--json` output, error cases, and sort-order invariants
- MCP server integration test suite (`benchmark/test_mcp.py`) — all 6 MCP tools tested via real JSON-RPC stdio

### Changed
- MCP tests made repo-agnostic via fixture discovery from live index files
- `--claude-md` symbol section wrapped in `symbolindex` code fence

### Docs
- Claude coding workflows section in README
- `lookup`, `dependencies`, and `high-blast` CLI command documentation
- MCP registration instructions corrected to use `claude mcp add`

## [0.1.0] - Initial release

### Added
- Multi-language dependency analysis: Python, JavaScript/TypeScript, Go, Ruby, Rust, Java/Kotlin, PHP, CSS
- Blast-radius impact scoring — every file gets a score based on direct and transitive dependents
- `codeindex analyze <repo>` — analyze a repo and write `codeindex.json`
- `codeindex impact <file>` — show blast-radius impact report for a file
- `codeindex symbols <repo>` — build `symbolindex.json` with functions, classes, and exports; supports `--inline` and `--claude-md` modes
- `codeindex serve --mcp` — MCP stdio server exposing `analyze_repo`, `get_impact`, `get_dependencies`, `get_high_blast_files`, `build_symbol_index`, `lookup_symbol`
- `codeindex serve --viz` — visualization UI server
- `codeindex install-hook` — pre-commit hook for blast-radius warnings
- Phase 4: Docker, CI/CD, and schema analyzers
- Phase 5: monorepo and cross-language intelligence
- Apache 2.0 license
