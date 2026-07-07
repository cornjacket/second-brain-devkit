# Big-brain — a shared brain (two ways to build it)

**Status:** roadmap / design-only — details to be hashed out, nothing built. A **shared**
brain (many people/clients) vs. the local-first single-user brain. There are two very
different ways to build it, and **the simpler one may be enough** — so this doc leads
with it.

---

## 0. The current brain has no sync layer (the gap that motivates this)

Verified: `new_brain.py` `git init`s a **local** repo with **no remote**, and both hooks
are purely local (embed + hydrate). Nothing ever pulls, pushes, or fetches.

- **Fine for the stated scope** — single user, single machine, local-first. There's no
  remote, so there is nothing to be inconsistent *with*.
- **A real gap the moment anything is shared** — multi-machine (laptop + desktop),
  backup, or multi-user. Today you'd have to add a remote by hand and remember to
  push/pull yourself, and the design does nothing to keep local ↔ remote consistent:
  no *pull-before-read*, no *commit + push-after-write*, and no *rebuild-cache-after-pull*.
  So two machines **would** drift. Not a bug in single-machine use; a genuine limitation
  for anything shared.

Approach A below turns this gap into the feature.

## Approach A — shared git remote (distributed, keeps local-first) ← start here

Put the vault in a **shared git remote** (GitHub/GitLab/self-hosted). Every user clones
it and runs the **same local-first brain** (SQLite cache, Ollama, hooks). "Sharing" is
just git sync — no cloud services, no rewrite:

- **Before reading/searching:** `git pull`, then rebuild the local cache from the pulled
  sidecars (`hydrate_cache.py` / `update_cache.py`). Now you see peers' notes.
- **After writing a note:** commit (the pre-commit hook embeds it locally) → `git pull
  --rebase` → `git push`.
- **Concurrency = git merge.** Different notes → clean auto-merge. The same note edited
  twice → an ordinary (rare) merge conflict, resolved by hand. No central lock needed.
- **The cache stays per-user, derived, git-ignored** → it never conflicts; each user
  rebuilds it locally after a pull.
- **Sidecar policy is the crux ([OQ-3](../open-questions.md)).** Today `.embed.json`
  sidecars are git-ignored (a single-user assumption). For a shared brain, either:
  - **commit the sidecars** — a peer then searches pulled notes with **no re-embed** (a
    vector is a vector; works given the same-model invariant), or
  - keep them ignored and have **each user re-embed** pulled notes locally (needs Ollama
    + the same model).
  Committing sidecars is simplest for a team; it just requires everyone use the **same
  embedding backend/model**.

**What's missing to make this real:** a small `sync` helper (a script and/or a hook)
that runs pull → rebuild-cache and commit → pull --rebase → push, so users don't have to
remember the dance — plus flipping the sidecar-commit policy. That's the whole feature:
no new services, still local-first.

**Best for:** a small team (or one person across machines) who all run the brain locally
(CLI / Claude Desktop).

## Approach B — deployed, centralized (Postgres + S3 + Lambda)

For clients that **cannot run the brain locally** (a browser / claude.ai-web, a
no-install user) or when you want one **authoritative central store**. This is the
"hosted brain, separate security model" that [mcp-server.md §2](mcp-server.md) deferred.

```
   many clients (HTTP / remote MCP / web)
                │
                ▼
        AWS Lambda  (stateless brain logic: search / get / add)
          │   │   │
          │   │   └─ cloud embedding API ── embed queries & notes (no local Ollama)
          │   └───── Postgres + pgvector ── concurrent vector index (KNN)
          └───────── S3 (markdown notes)  ── durable source of truth
```

- **Compute — AWS Lambda:** stateless, scales, concurrent invocations.
- **Notes — S3:** replaces the local git vault as the durable store.
- **Vector index — Postgres + `pgvector`:** replaces the SQLite `vec0` cache; **MVCC
  gives real concurrent readers + writers**, which **retires the SQLite-only
  [OQ-5](../open-questions.md#oq-5) WAL / in-place-hydrate / `flock` layering** for this
  variant (the local brain keeps SQLite).
- **Embedding — a cloud API** (Bedrock Titan / Voyage / OpenAI / hosted `nomic`), since
  Lambda has no local Ollama; the same-model invariant still holds corpus-wide.

**Cost:** it requires abstracting the three seams the code hardcodes today — **store**
(git-vault → S3), **cache** (sqlite-vec → pgvector), **embedder** (already abstracted →
add a cloud backend) — following the `embedder.py` env>config>fallback pattern. A real
refactor, plus auth and a running Postgres.

## Which one?

- **Approach A** if every user can run the brain **locally** — it reuses everything,
  stays local-first, and the only new work is a sync helper + the sidecar-commit policy.
  **Start here.**
- **Approach B** only when you need a **hosted / web / no-install** brain or a single
  central authoritative store. Much bigger lift.

They're **not mutually exclusive**: A is the near-term "shared brain among local users,"
B is the long-term "hosted brain for clients that can't run it." A also fixes the §0 sync
gap for the ordinary single-user-multi-machine case, independent of any team use.

## Open questions — to hash out

- **A:** sidecar-commit vs. re-embed (revisits [OQ-3](../open-questions.md)); the `sync`
  helper's shape (script vs. hook vs. wrapper); merge/conflict UX; do you also push the
  git-ignored cache? (no — keep it derived/local).
- **B:** auth & multi-tenancy; write consistency when the store (S3) and index (Postgres)
  are separate services; embedding provider + cost; privacy/data-residency (a shared
  cloud brain is the explicit opposite of local-first).
- **Both:** the write path — how a client **adds** a note (ties to the `add_note` design,
  PLAN G6 / task #5).

**Local-first must not be eroded to enable either.** Nothing here is started.
