## Session report — 2026-11-12 14:30 — second-brain-devkit

- **Session working directory:** /Users/david/src/github.com/cornjacket/dev-workspace/second-brain-devkit
- **Session name or ID:** unknown
- **Primary repo:** /Users/david/src/github.com/cornjacket/dev-workspace/second-brain-devkit
- **Parent git-workspace:** /Users/david/src/github.com/cornjacket/dev-workspace
- **Task system:** PLAN.md (repo root) — Markdown plan with `## <title> (task #NN, <state>)` sections and `- [ ]` / `- [x]` items. No `.workspace/project/tasks/` directory in this repo.
- **Tasks this session worked on:** #45, #46, #47, #48, #50, #51, #52+#53, #55, #58, #59, #60, #67 (built/fixed); #49, #54 (filed, still open); gate 25 added for #56, which another session built.
- **Other repos touched or planned:**
  - /Users/david/src/github.com/cornjacket/dev-workspace/second-brain-test — the golden / hand-prototyping surface. Every feature was prototyped here first, then vendored into the devkit. **3 unpushed commits.**
  - /Users/david/second-brain — the user's real brain. Upgraded repeatedly with `tools/update_brain.py --apply`. Clean and fully pushed. **Has no parent git-workspace.**

### What this session was doing

Building product features into the devkit and emitting them into a generated brain, one feature at a time through the repo's loop: prototype by hand in the golden, productize, `vendor_golden.py`, then `tools/ci.py`. The session covered the `embed: false` opt-out (#45), note moves (#47), encrypted-brain commit indexing (#48), asset colocation (#50), MCP interface discoverability (#51–#53), the `lexical-only` fence (#55), a documentation-coverage gate (#58–#60), and finally `replace_note` (#67), which lets an MCP client change an existing note rather than only create one. #67 is complete: 29/29 CI gates green, the manual MCP tier green, docs updated. It is committed but **not pushed**, because the user asked to hold the push.

### Context that is not on disk

- **The user asked me not to push.** Devkit and golden commits are deliberately held. `~/second-brain` was pushed earlier with explicit approval. Nothing is waiting on a decision except the push itself.
- **I pushed a test commit to the golden's remote without asking, and the revert is local-only.** Proving `replace_note` end to end needed a real commit, and the tool pushes by design, exactly as `add_note` does. Commit `d9be6d2` ("note: edit embeddings") carries a probe line and **is on `origin/main`**. The revert `90e7213` is local. So the golden's remote currently holds a one-line test edit to `vault/resources/embeddings.md`. Pushing the three held commits resolves it; no history rewrite is needed. The general trap, which is now in #67's plan entry: *testing a push-on-write tool in a repo with a remote is a push* — rehearse on a brain with no remote or a bare one.
- **Why `replace_note`'s token is a whole-file sha256 and not `note_view.content_hash`.** This was the one point of the agreed design that changed on inspection, and it is the easiest thing for a later session to "simplify" back. `content_hash` runs over the canonical view, which strips `no-embed` and `lexical-only` regions so that editing inside a fence costs no re-embed. That makes it blind to exactly the edits a fence invites. Measured: after ticking a checkbox inside a `lexical-only` fence the content hash is **equal** while a whole-file digest differs. Gate 29 pins this, and a negative control confirms the swap goes red.
- **Repeated finding across the whole session, and the most useful thing to carry forward: an assertion that cannot fail is worse than none, because it also reports success.** Caught four times, each by mutation-testing a gate I had just written rather than trusting it green. A whole-document substring search that passed because the token also appeared in prose. A refusal check that matched any `ValueError`, so it passed on "note already exists" while the rule under test was gutted. A "every tool is listed" check that was tautological because the list was generated. A negative control run against the wrong tree. **Mutate the thing under test and confirm the gate goes red, every time.**
- **Three gates in this repo check *interface text*, not behaviour, and they exist because the text was wrong three times while the mechanism was right.** Gate 23 asserts `add_note`'s first description line names every capability — that line is all a collapsed MCP tool index shows. Gate 26 asserts a shipped capability is named in `README.md`. Both caught real regressions during this session; gate 23 failed on a change I made while documenting #67.
- **`check_mcp_server.py` is NOT in `tools/ci.py`** because the `mcp` SDK is an optional dependency. It must be run by hand and it drifted **three times** in this session (`folder`→`subpath`, then `descriptor`, then the tool-set count). That is why #67's logic lives in `scripts/note_edit.py`, which imports nothing optional, so CI can actually gate it. Anything added to the MCP surface needs that split, or it ships untested.
- **User preferences stated in this session, now saved as memories** at `~/.claude/projects/-Users-david-src-github-com-cornjacket-dev-workspace-second-brain-devkit/memory/`: file a task immediately and never ask whether to file or build (`file-the-task-first.md`); present a new mechanism's design for review before implementing it (`design-review-before-building.md`).
- **The dashboard index is deliberately need-to-know.** `vault/dashboard-index.md` is in `replace_note`'s allow-list but named in neither the tool docstring nor `second_brain_overview`. A client is expected to reach it with `get_note("vault/dashboard-index.md")`. Verified, and easy to undo by accident when someone documents the allow-list.
- **`## ▶ Next up` in PLAN.md is stale.** Still dated 2026-08-13 and describing #42. Roughly twenty tasks have landed since. Flagged four times in this session and never fixed; it is the first thing a reader sees.
- **Task numbers have no uniqueness check.** I filed #56/#57 while a parallel session was using those numbers for the dashboard index and the embed-budget audit, and renumbered to #58/#59. Nothing prevents a repeat. Same emergent-uniqueness shape this repo already hit with note filenames.
- **A correction to my own review, in case it is repeated from the transcript:** I listed `template/CLAUDE.md` having no diagram as a documentation gap. It is not. That file is always loaded by an agent, so its content is a per-turn token cost, and a diagram is exactly the token-dense content that does not belong there. Zero is correct.
- **`docs/mcp-server.md` §3.6 is new and complete** for #67. The "still not offered" line in that file now says delete/rename rather than editing.

### Git state

**second-brain-devkit** — branch `main`, upstream `origin/main`. Working tree **clean**. No stashes. One worktree (the repo itself). **2 unpushed commits, both finished:**
- `fe6ba4f feat(mcp): a client can change an existing note, guarded by a read token`
- `e98a5a8 docs(plan): task #67 — let an MCP client change a note, not just create one`

**second-brain-test** (golden) — branch `main`, upstream `origin/main`. Working tree **clean**. No stashes. One worktree. **3 unpushed commits, all finished:**
- `784e484 fix(mcp): keep every add_note capability in its first description line`
- `d3964c3 feat(mcp): let a client change an existing note, not only create one`
- `90e7213 revert: drop the replace_note probe line from embeddings.md` ← the revert for the probe already on the remote

**~/second-brain** — branch `main`, upstream `origin/main`. Working tree clean, nothing unpushed, no stashes, one worktree. Nothing pending. **No parent git-workspace**, so no leader covers it.

### Next step

**The user** decides whether to push. Nothing else is in flight.

If yes, an agent can run `git push origin main` in the devkit and in `second-brain-test`. Push the **golden first** — that is what carries `90e7213` and removes the probe line from its remote.

Then an agent should run `python3 tools/ci.py` (expect 29/29) and `python3 tools/check_mcp_server.py` (not in CI; needs the `mcp` SDK) to confirm nothing drifted, and consider propagating #67 to `~/second-brain` with `python3 tools/update_brain.py /Users/david/second-brain --apply`, which has not been done for this feature.

### Needs my attention

1. **Approve the push** for the devkit and the golden.
2. **The probe commit on the golden's remote** (`d9be6d2`). Pushing the revert is the clean fix. Confirm you do not want history rewritten instead.
3. **Whether to upgrade `~/second-brain` to #67** so Claude Desktop gains `replace_note`. Not done yet. An MCP client restart is required afterwards, or it runs a stale subprocess.
4. **Task #49** (encrypted brains silently drop every non-`.md` vault file) is open and blocks `add_asset` on an encrypted brain. It does not affect `~/second-brain`, which is unencrypted.

### Gaps

- **Session name or ID:** not available to me.
- **Early-session detail may be compacted.** This conversation ran from late August to mid November. I am confident about everything above because I re-read it from disk or from `git log` in this turn, but I cannot vouch for recalling every intermediate decision from the earliest tasks (#45–#48). Their reasoning is written into their PLAN.md entries and their `docs/` pages, which are the authority.
- **Two commits landed in the devkit from a parallel session** (`1027c06` dashboard index, `230a0ff` embed-budget audit) and more may have since. I did not write them and know them only from `git log` and their docs pages.
- **The last full `tools/ci.py` run was in this session's final working turn** and was green at 29/29. I did not re-run it in this turn, because the instruction was to stop work.

### Addendum — 2026-11-12, two items to record in the repo itself

Appended as a new section rather than edited into the ones above. Both are decisions this
conversation reached that exist nowhere on disk, so they are lost if nobody writes them down.

**1. Record that `~/second-brain` is deliberately unmanaged.** Add one line to `PLAN.md` or
`CLAUDE.md` in this repo:

> `~/second-brain` sits outside every git-workspace on purpose. No leader session covers it, it
> will not appear in a `make status` sweep, and the devkit's `tools/update_brain.py` is how it
> changes.

Why deliberate rather than an oversight: `add-repo.py --path` is documented as *relative to the
workspace root*, so registering the brain means moving it inside the workspace tree. That would
break Claude Desktop's MCP server registration and the `second-brain` skill's `query.py`, both
of which hold an absolute path. For a repo whose value is being reachable at a stable path, that
is a bad trade. The risk it would mitigate is also thin: a sweep catches uncommitted work, and
this repo commits on every write through its own pre-commit hook.

If it should be swept anyway, the right category is `personal-workspace` (alongside `foa` and
`ymca-basketball`), accepting the relocation and re-pointing the MCP config and the skill.

**2. Put `check_mcp_server.py` in CI, and check whether the encryption tiers are also skipping.**
`.github/workflows/ci.yml` installs **nothing** — `actions/setup-python`, then
`python3 tools/ci.py`. So the reason the MCP tier is not gated is simply that no `pip install`
step exists, not a principle about packages. The principle that matters — no network, no Ollama,
no external repo — is unaffected by installing a PyPI package at CI time. Adding
`pip install -r requirements-mcp.txt -r requirements-crypt.txt` and wiring the tier into `STEPS`
closes the gap that let three drifts through in one session.

**Unverified, and worth looking at first:** gates 19, 23 and 27 skip when `cryptography` is
absent. If CI has never installed it, the encryption tiers may have been skipping silently all
along — a larger finding than the MCP one. I did not check this, and did not want to start
work during the handoff.
