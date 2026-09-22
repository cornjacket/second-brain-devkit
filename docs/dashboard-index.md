# Dashboard index — the brain reports its own state (task #56)

A brain could relate notes four ways and report state in none of them. A **folder** says
what archives together. A **tag** says what a note is about. An **embedding** says what is
similar. A **wikilink** says what is related. Not one of them knows that a checkbox is
unticked, or that a project has been waiting three weeks on somebody else's reply.

**Similarity is not state.** Answering "where am I?" meant opening notes one at a time and
re-reading them, which is exactly the work a second brain exists to remove.

| | Step | What it entails |
| --- | --- | --- |
| ✅ | 1. Prototype | `vault/dashboard-index.md` + a CLAUDE.md pointer, by hand in the golden. |
| ✅ | 2. Seed it | `seeds/dashboard-index.md`, so a new brain is born with one. |
| ✅ | 3. Reach existing brains | `VAULT_SEEDED` in `update_brain.py` — create if absent, never overwrite. |
| ✅ | 4. Gate it | Both halves asserted in `check_claude_block.py`; mutation-tested. |

## Where it lives, and why that is the whole design

`vault/dashboard-index.md` — the **vault root, outside every PARA root**.

The indexer walks `vault/{projects,areas,resources,archive}`. A file at the vault root is
therefore **never embedded, by construction**. That is deliberately *not* an `embed: false`
opt-out (task #45): an opt-out is a flag that can be forgotten or mistyped, and the parser
fails open, so a mistake means the status table silently joins the corpus. Placement cannot
be mistyped. The same mechanism already exempts `vault/templates/`.

It should not be searchable anyway, for two reasons that point the same way:

- **You never need to search for a file whose path is a constant.** Search earns its keep on
  notes whose location you have forgotten. This one has a fixed address, and `CLAUDE.md`
  hands that address to the agent.
- **It would poison results.** A status table churns on every change and is mostly project
  names — a bad vector that would then compete against the notes holding the actual
  knowledge, on precisely the queries where those notes matter most.

## The contract: point, don't copy

The file holds **one row per active effort**: next action, blocked-on, last touched. It
links to the note that owns a task and **never mirrors that note's checklist**.

A copied checkbox has two homes and drifts the first time the wrong one is ticked — at which
point the dashboard is not stale but *lying*, which is worse than empty. What earns a row is
what exists nowhere else: the **judgment** about what comes next, and the **blocked-on**,
which is invisible inside the notes because you cannot see it without re-reading a whole file.

The exhaustive list stays one `grep -rn '^- \[ \]' vault` away, so there is no reason to keep
a copy of it. Checkboxes belong **inside the note that owns them** — dated `- [x]` lines keep
*why* and *when* beside the decision, which a separate task app throws away.

## VAULT_SEEDED — a third thing `update_brain` can do

`update_brain.py` had two behaviours for a path, and this file wants neither:

| | Behaviour | Wrong here because |
| --- | --- | --- |
| `VAULT_OWNED` | overwrite every upgrade | the file **is** the user's live status; clobbering it turns routine maintenance into data loss |
| `PRESERVE` | never write | an existing brain would never receive it, which is the reason it lives in the devkit at all |

So: **create if absent, never overwrite.** A brain lacking the file is offered it as `NEW`;
a brain that has one reports `SKIP` with a reason and is never queued for a write.

Two consequences worth naming rather than discovering:

- **A seeded file never receives an improvement.** Revise the contract later and brains
  created before the revision keep the old text. That is the right trade *because the
  contract worth keeping current lives in the managed `CLAUDE.md` block*, which every brain
  does receive on every upgrade. The file is a starting point, not a source of truth.
- **`_is_preserved()` still answers True for it.** That function declares *ownership*, and a
  seeded file is the user's from the moment it lands; only its first creation comes from the
  devkit. Saying False there would also assert the file is machinery, which
  `check_content_classification.py` reads as "encryption must not cover it" — the opposite of
  true for a file listing your projects. Seeding is an explicit pass in `plan()` instead.

## Encryption refuses it, and the gate is what found that

An **encrypted** brain is skipped outright, reported as `SKIP … encrypted brain — the vault
is yours alone; create it yourself`.

Encryption covers the *whole vault*, not the PARA roots (see `content_notes()`), so it owns
this file too — correctly, since a list of your projects and who you are waiting on is
exactly the content encryption exists for. But an encrypted brain git-ignores `vault/` and
commits ciphertext, so a plaintext file written there would be neither encrypted nor
committed: **present on disk and silently not backed up**, the failure `encrypt_vault`'s own
docstring calls the hard one to notice.

This was not foreseen. Gate 18 (`check_content_classification.py`) caught it on the first run
after `_is_preserved` was loosened — the invariant *every `.md` is content or machinery, and
update_brain never writes content* is precisely what a new write path is liable to break.

## What is gated

`check_claude_block.py`, both directions, because each failure hides in the other:

- an edited dashboard survives `--apply` byte-for-byte, and never appears as `CHANGED`
- a brain missing the file receives it, matching the shipped seed

A dashboard that never arrives looks like a brain that simply has none; one that gets
overwritten looks like a successful update until you open it. Mutation-tested: turning the
skip back into a write turns the gate red.
