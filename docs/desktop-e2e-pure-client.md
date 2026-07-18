# Pure-client cross-session retrieval test — Desktop only, no local verifiers (task #36)

**Status:** **PLANNED — ▶▶ proposed** (2026-07-17). Complements the #33/#34/#35 suite
([desktop-e2e.md](desktop-e2e.md)); no code yet.

## 1. Why — the two things the existing suite cannot prove

The emitted `desktop-e2e/` suite (#33/#35) pastes prompts into Desktop but **verifies with local
scripts** (`verify_*.py` reading files + `git log`) and runs the whole thing **in one chat
session**. That leaves two gaps it structurally cannot close:

- **Does retrieval actually work *through Desktop*, end to end?** The verifiers confirm a note was
  *written*; they never ask Desktop to *find it back*. A brain that ingests perfectly but whose
  search is broken in the real client would still pass.
- **Is the answer coming from the brain, or from the chat?** When you ingest and then query in the
  **same** session, the model can answer from its own conversation memory — it saw the note text
  minutes ago. That is indistinguishable, from the outside, from real retrieval. The suite can't
  tell them apart.

This test closes both by being **pure black-box**: seed via Desktop, **throw the conversation
away**, then retrieve in a **fresh** session using nothing but the brain's own tools. If the
seeded value comes back, retrieval genuinely works and genuinely persisted — because there is no
conversation left to remember it.

## 2. The protocol (human-driven, no verifier scripts)

Three phases, all in Claude Desktop, nothing run locally except optional setup/teardown (§5):

1. **Ingest — Session 1 (a new chat).** Paste the ingestion prompts. Each seeds a **canary
   value**: a distinctive, invented token that cannot be in the model's training data or already
   in the brain (see §3). Confirm each write is acknowledged.
2. **Forget — delete the chat session.** This is the load-bearing step. Deleting the chat removes
   the only place the model could be "remembering" the seed from. (Even just starting a new chat
   works; deleting is the strongest form.)
3. **Retrieve — Session 2 (a fresh chat, zero shared context).** Paste the query prompts. The
   model must reach the brain via its MCP tools and return the canary. **The human reads the
   reply** and confirms the seeded value came back — that is the entire oracle. No script.

## 3. What makes a result trustworthy (design rules)

- **Canary values, not real facts.** Seed something like *"The Zephyr-Q7 ingestion codeword is
  `marmalade-quasar-19`."* A hit on `marmalade-quasar-19` in a fresh session can only mean the
  brain returned it — the model can't have guessed a token it never saw. Seeding a real, guessable
  fact (e.g. "Paris is the capital of France") proves nothing: the model knows it without the brain.
- **Aim each query at the right substrate** — the [[unfindable-is-not-nonexistent]] trap. The brain
  has **distinct retrieval layers with distinct blind spots**: PARA notes are in the semantic index
  (reachable by `search`), but glossary terms are **embedding-excluded** (reachable only by
  `lookup_glossary_term` / `list_glossary_terms`), and tags by `list_tags`. A canary seeded as a
  glossary term but queried via semantic search will **falsely read as "not found."** Pair every
  seed with the query that targets its own substrate:

  | Seed (Session 1) | Query (Session 2) | Correct substrate |
  |---|---|---|
  | a note whose body contains a canary sentence | "search the brain for `<canary>`" | semantic search |
  | a glossary term with a canary definition | "look up the term `<canary-term>`" | glossary lookup (not embed) |
  | a note tagged with a canary tag | "list the brain's tags / notes tagged `<canary-tag>`" | tag listing |

- **The human holds the ground truth.** Because you know exactly what was seeded, a miss is an
  **unambiguous FAIL**, not "maybe it's just unfindable." That is what turns a black-box eyeball
  into a real assertion.
- **Negative control (optional).** In Session 2, also query for a canary that was **never seeded**.
  The brain must **not** return it and the model must not fabricate one — this catches the failure
  mode where an assistant confabulates an answer rather than reporting a true absence
  ([[unfindable-is-not-nonexistent]]).

## 4. Why this is separate from #33/#35, not a merge

#33/#35 are **fast, deterministic, single-session, script-verified** — good for "the write path +
tool surface still work." #36 is **slow, human-judged, multi-session, script-free** — the only way
to prove *retrieval + persistence through the real client, uncontaminated by chat memory*. Same
spirit (assert what a Python MCP client can't show), different failure class. Keep both.

## 5. Cleanup — reuse the #34 disposable branch

The ingestion prompts **write to the vault** (real commits), and the two phases span a delete +
restart, so the writes must **persist between sessions** (they do — the branch + index live on
disk regardless of chat state). Run the whole thing on the #34 disposable branch: `setup.sh`
before Phase 1, `teardown.sh` **after** Phase 3 (never between — teardown deletes the branch and
its notes). This keeps a real brain pristine. Setup/teardown are the *only* local scripts involved,
and they are cleanup, not verification.

## 6. Scope & deliverables

- Human-driven **release/installation acceptance**, **not** a CI gate (no API drives Desktop's
  GUI, and the oracle is a human reading replies).
- Deliverables: ingestion + query **prompt pairs** with embedded canaries and a short human
  checklist — likely `desktop-e2e/pure-client/` (ingest-NN / query-NN prompt files + README).
- **Open — emit it too?** Like #35, this could ship inside every brain so a user can self-verify
  retrieval, not just the write path. Decide when building: emit (prototype in the golden,
  `verbatim` in `emit-manifest.toml`) vs keep devkit-only.
- **Open — canary hygiene across runs.** Reusing the same canary token risks a later run "finding"
  a leftover from an earlier one. Either vary the token per run (a date/word suffix the human picks)
  or rely on teardown to remove the seed notes each time.
