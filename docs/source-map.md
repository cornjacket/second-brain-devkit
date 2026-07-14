# Source map — what every file is for

A one-line purpose for each source file, grouped by role. Two families: the **emitted
brain** (what every generated brain ships) and the **devkit** (the generator +
validation, never emitted).

- *Complements, doesn't replace, [`emit-manifest.toml`](../emit-manifest.toml)* — the
  manifest is the source of truth for **how** each file is emitted
  (`verbatim`/`cleaned`/`generated`/`exclude`); this doc says **what** it does. If a
  file is added/removed, update both (the partition check enforces the manifest side).
- Each script also carries a module docstring with the fuller story.

---

## A. The emitted brain (`scripts/`, `skill/`, hooks, config)

Everything a generated brain owns and runs. Lives in the golden at
`../second-brain-test/`, vendored to `tests/golden/`, emitted via `template/`.

### Embedding & cache pipeline (`scripts/`)
| File | Purpose |
|---|---|
| `embedder.py` | Embedding backends (`test` / `ollama`); resolves the active backend (env var > `config/embedder.toml` > `test`) and exposes `embed(text)→vector` + `EMBED_DIM`. The same-model choke point. |
| `db.py` | Opens SQLite with the `sqlite-vec` extension loaded (stdlib `sqlite3`, else `apsw` fallback); applies `WAL` + `busy_timeout` PRAGMAs (OQ-5 layer 1). |
| `embed_staged.py` | Pre-commit helper — (re)generate `.embed.json` sidecars for **staged** PARA notes. |
| `embed_vault.py` | Bulk-embed **every** PARA note in the vault, refreshing sidecars. |
| `hydrate_cache.py` | Full rebuild of `data/brain.db` from all sidecars, in one **in-place** transaction (OQ-5 layer 2). |
| `update_cache.py` | Incremental cache updates, one note at a time (`--upsert`/`--delete`/`--from-commit`) — no teardown. Driven by the post-commit hook. |
| `search_vault.py` | Semantic search over the vec0 cache; exposes the reusable `search()` (shared by CLI, skill, MCP) plus a CLI. |

### AI interface (reach the brain from elsewhere)
| File | Purpose |
|---|---|
| `skill/second-brain/SKILL.md` | Skill manifest — its `name`+`description` drive proactive "consult before designing" use in Claude Code / Gemini CLI. |
| `skill/second-brain/query.py` | Skill entry point — resolves the brain root through the install symlink, ensures the cache, forwards to `search_vault`, prints **absolute** note paths. |
| `scripts/mcp_server.py` | MCP **stdio** server for **Claude Desktop** — search/fetch/browse/glossary, plus the one writer `add_note`, which **commits + pushes** (the commit is what embeds). See [mcp-server.md](mcp-server.md). |
| `scripts/install_skill.py` | Install/uninstall the skill (symlink) for Claude/Gemini; `--global`/`--project`, `--nudge`, `--apply`-gated. |

### Health, setup & housekeeping
| File | Purpose |
|---|---|
| `doctor.py` | "Is this brain ready?" preflight — deps, Ollama reachability/model, full vault↔sidecar↔db consistency, with `--repair`. |
| `self_test.py` | Deterministic **structural** self-test (`test` backend, byte-exact fixtures) — a CI gate. |
| `check_line_count.py` | Markdown line-count guard (pre-commit warning). |
| `seed_vault.py` | Seed/reset the PARA vault from the canonical `seeds/` (the generation post-step). |
| `register.py` | Register a project repo with this brain. |

### Hooks, config, deps
| File | Purpose |
|---|---|
| `.githooks/pre-commit` | Embed staged notes (`embed_staged`) + run the line-count guard. |
| `.githooks/post-commit` | Refresh the cache after a commit (`update_cache --from-commit HEAD`). |
| `config/embedder.toml` | Per-brain default backend (`ollama` in a generated brain; `test` in the golden). |
| `requirements.txt` | Core deps — `sqlite-vec`, `apsw`. |
| `requirements-mcp.txt` | Optional MCP SDK (`mcp`), isolated so core + CI stay lean. |

---

## B. The devkit (generator + validation — never emitted)

Lives only here, under `tools/`. Never copied into a brain.

### Generator
| File | Purpose |
|---|---|
| `tools/generate.py` | The generator **core** — `generate(target, params)` copies `template/` → target + runs the `seed_vault` post-step. The pure function both modes call. |
| `tools/create_second_brain.py` | **Mode B** (production) — generate a real brain you own: `generate` + `git init` + first commit. The end-user entry point. |
| `tools/update_brain.py` | **Lifecycle (G4)** — non-destructively upgrade an existing brain's tooling from `template/` (dry-run; `--apply` commits). Preserves `vault/`/`data/`/`config/`/`CLAUDE.md`/`GEMINI.md` + history. |
| `tools/run_sandbox.py` | **Mode A** harness — wipe `sandbox/scratch/`, regenerate, and run the gates. |

### Template / golden machinery
| File | Purpose |
|---|---|
| `tools/vendor_golden.py` | Snapshot the live golden's tracked files into `tests/golden/` (a dev-machine step; CI never runs it). |
| `tools/build_template.py` | Build `template/` from `tests/golden/` + `emit-manifest.toml` (verbatim copy + clean the `cleaned` files). |
| `emit-manifest.toml` | Source of truth for the emitted file set + its classification (partition-enforced). |

### Validation guards (all run by `ci.py`)
| File | Purpose |
|---|---|
| `tools/ci.py` | The full acceptance gate (9) — one entry point for local **≡** CI (partition → template-in-sync → Mode-A → Mode-B smoke → note-gate). |
| `tools/check_manifest_partition.py` | Verify `emit-manifest.toml` partitions the golden's tracked files exactly. |
| `tools/check_no_forbidden_refs.py` | Grep the emitted tree against the denylist (`ai-project-status`) — zero hits. |
| `tools/check_structural_diff.py` | The Mode-A acceptance oracle — generated tree **==** golden, byte-for-byte. |
| `tools/check_semantic_retrieval.py` | Opt-in Ollama retrieval-quality check (SKIP + exit 0 when Ollama absent). |
| `tools/check_config_matrix.py` | **Gate 10** — exercises every `config/features.toml` toggle **off its default** (n+1 runs, not 2^n), because #28 shipped through a green suite whose only file-modifying hook was off by default. **Derives the toggle space from `features.toml`, so a new toggle with no coverage FAILS the build.** Names its uncovered gaps (toggle interactions, the `ollama` backend) rather than implying coverage. |
| `tools/check_note_gate.py` | **Gate 9** — the "what earns a note" editorial gate must be identical in `CLAUDE.md` (the in-repo agent's always-loaded copy) and `seeds/templates/new-note.md` (the only copy Claude Desktop can reach, via `get_note_template()`). Deliberate duplication, disjoint audiences; `--sync` rewrites the mirror from the canonical. |
| `tools/check_mcp_server.py` | Opt-in behavioral MCP check — drives the emitted stdio server (test backend); asserts the seven-tool surface, **no `outputSchema`**, search + glossary tools, the #21 negative suite (traversal refusals, substrate disjointness, glossary embedding-free — against a brain whose vector cache is poisoned), and the #5 write path (add_note commits + pushes to a bare remote, is searchable at once, cannot escape the vault via the title, and never sweeps a user's staged work into its commit). SKIP when `mcp` absent. |

---

## Where the design lives (docs/)
| Doc | Covers |
|---|---|
| [`SPEC.md`](../SPEC.md) | System & generator spec (workflow, roles, lifecycle, validation loop). |
| [`mcp-server.md`](mcp-server.md) | MCP server design, verify recipe (§10), Claude Desktop `outputSchema` gotcha (§11). |
| [`retrieval-quality.md`](retrieval-quality.md) | Planned hybrid FTS5 search + nomic embedding prefixes. |
| [`claude-desktop-workflow.md`](claude-desktop-workflow.md) | End-to-end Claude Desktop walk-thru. |
| [`remote-backed-brains.md`](remote-backed-brains.md) | Task — connect a new brain to a git remote at creation (`--remote`). |
| [`big-brain.md`](big-brain.md) | Roadmap — shared brain (git-remote sync, or Postgres/S3/Lambda). |
| **this file** | What every source file is for. |
