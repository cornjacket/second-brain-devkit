# Second Brain — Agent Memory

You are working **inside a Second Brain**: a PARA Markdown vault (for humans) plus
a local SQLite `vec0` cache (for you). The full design contract lives in
[second-brain-devkit](https://github.com/cornjacket/second-brain-devkit) (which generated this
brain); this file is the operational memory.

> `GEMINI.md` is a symlink to this file so Claude and Gemini read identical
> instructions.

## Recording knowledge

Durable lessons, insights, and architecture understandings belong here as **PARA
notes** — there is no separate ingestion path; a note *is* the ingestion.

- File the note under the right PARA root inside the vault: `vault/projects/`
  (goal-bound effort), `vault/areas/` (ongoing responsibility), `vault/resources/`
  (durable reference), `vault/archive/` (inactive).
- Lowercase kebab-case filename, `.md`, with YAML frontmatter (`tags: [...]`).
  Link related notes with `[[wikilinks]]`. Start from the annotated example at
  [`vault/templates/new-note.md`](vault/templates/new-note.md) — copy it into the
  right PARA root and fill it in (the template dir isn't indexed).
- Commit it. That's the whole flow: the **pre-commit** hook embeds the note into
  its `.embed.json` sidecar and the **post-commit** hook refreshes the cache, so a
  committed note is **searchable immediately** — no manual step. (`hydrate_cache.py`
  stays available for a manual/bulk rebuild, e.g. after `embed_vault.py`.) Vault
  sidecars are **derived and git-ignored** (regenerated locally) — do not hand-edit
  or commit them. The only committed sidecars are the deterministic fixtures under
  `tests/fixtures/vault/`.

## Querying knowledge

Before solving something from scratch, search what the brain already knows:

```bash
python3 scripts/search_vault.py "<natural-language query>"
```

After adding or editing notes, rebuild the cache:

```bash
python3 scripts/hydrate_cache.py
```

## Invariants & safety

- **Same model for notes and queries.** Search only works if the query is
  embedded by the same backend/model as the notes. Both go through
  `scripts/embedder.py`; do not bypass it. The backend is set once in
  `config/embedder.toml` (`ollama` = real semantic search; `test` = deterministic
  plumbing) and overridable per-command with `SECOND_BRAIN_EMBEDDER`.
- **Never** edit a `.embed.json` sidecar by hand or let git conflict markers into
  one (`merge=binary` is enforced).
- **Never commit live-vault vectors** (they're machine/model-dependent, derived,
  git-ignored). Only the deterministic `test`-backend `tests/fixtures/vault/`
  sidecars are committed — and the committed fixtures are **pinned to `test`**: don't
  commit `ollama` fixtures. `scripts/self_test.py` verifies the fixtures byte-diff.
- **Never** add a cloud vector store. This brain is local-first.
- The cache (`data/brain.db`) is derived — safe to delete and rebuild anytime.

## First-time setup

```bash
git config core.hooksPath .githooks   # activate the embed hook
pip install -r requirements.txt        # sqlite-vec (+ apsw fallback)
```
