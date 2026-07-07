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

- **Before reading/searching:** `git pull`, then react to whatever it brought (see
  *"the post-pull reaction"* below), so the local cache reflects peers' notes.
- **After writing a note:** commit (the pre-commit hook embeds it locally) → `git pull
  --rebase` → `git push`.
- **The cache stays per-user, derived, git-ignored** → it never conflicts; each user
  rebuilds it locally after a pull.

**The post-pull reaction (new — this is essential, not optional).** A `git pull` is not
the end of the story: any PARA note it **adds or changes** must trigger the same local
reaction a commit does — *(re-)embed the note → hydrate/re-hydrate the cache* — or the
new/edited notes are invisible to search until then. The natural home is a git
**`post-merge` hook** (git's post-pull equivalent of the existing `post-commit` hook):
it runs `update_cache.py --from-commit` over the merged range, embedding what's missing
and rebuilding the cache. Without it, a user pulls new notes but can't find them.

**Embeddings in git — an optimization, not a requirement.** Whether the pull needs to
*re-embed* depends on the sidecar policy ([OQ-3](../open-questions.md); today `.embed.json`
sidecars are git-ignored):
  - **Commit the sidecars (optimization):** the pull brings each note's vector with it,
    so the post-pull reaction is **hydrate only — no re-embedding** (a vector is a vector,
    given the same-model invariant). Faster, and a peer without Ollama can still search.
    Cost: derived data in git + everyone must share the embedding model.
  - **Keep them git-ignored (strictly sufficient):** the post-merge hook **re-embeds**
    the added/changed notes locally (needs Ollama + the same model), then hydrates. Keeps
    git clean; costs each peer the compute.
  So committing embeddings is a **caching optimization** the shared repo *may* adopt —
  strictly, correctness only needs the per-user re-embed + hydrate.

**Merge conflicts need a human (or an AI) in the loop.** A `git pull` can hit a merge
conflict — most likely two users editing the **same note**. This **cannot be silently
auto-resolved**: a `sync` helper must **stop and surface** the conflict for the user (or
an agent) to resolve, then finish the embed/hydrate reaction on the resolved file. Upside:
notes are Markdown, so conflicts are human-readable and an AI can often resolve them; but
the sync path must treat "conflict → intervention required" as a first-class outcome, not
an error to paper over.

**What's missing to make this real:** a small `sync` helper (pull → post-pull reaction →
handle-conflicts; and commit → pull --rebase → push), most of the reaction living in a
`post-merge` hook that mirrors `post-commit`; plus the sidecar-commit policy decision.
No new services, still local-first.

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
