# MCP server hardening — nothing may hang the server (task #24)

**Status:** OPEN — four hang vectors to close (§2). The bug that *started* this (§1) turned out to
be a Claude Desktop approval dialog nobody clicked; **the server needs no change for it.**
**Scope:** the emitted `scripts/mcp_server.py` and `scripts/embedder.py`.
**Constraint that does not bend:** none of this touches the indexer's walk. `glossary/` and
`templates/` are excluded from the vector index *purely* by not being PARA roots — no exclusion
list, no config flag — and that must hold. Every fix below is inside the tool/subprocess layer.

---

## 1. The reported bug — a post-mortem (SOLVED; nothing to fix in the server)

**Report:** `add_note` hangs (no response, 4-minute client timeout) when `para_root` contains a
path separator (`"resources/test"`). Suspected cause: it gets past validation and blocks in `git
push`.

**Root cause: an unanswered tool-approval dialog in Claude Desktop. The server was never asked.**

`add_note` is the only **write** tool on this server; every other tool is read-only and had already
been approved. Desktop gates *dispatch* on approval, and approval is **sticky per tool**. The model
emitted one `add_note` call, Desktop raised an approval dialog, **nobody clicked it**, so the call
was never dispatched. After four minutes the model's tool slot was filled with Desktop's synthetic
message: *"No result received… the local MCP server may be unresponsive, crashed, or not running."*

Every clause of that message is false. The server was idle, healthy, had run continuously for
hours, and had never received the call. **That message is what sent the investigation into the
server for an hour**, and it is itself a Claude Desktop bug.

How it was proved (each step is falsifiable, and one killed the previous theory):

1. `para_root` **is** allowlist-validated (`if para_root not in PARA_ROOTS: raise`). Reproduced
   under Desktop's own minimal launchd env: **0.00 s, `isError=True`, no side effects.** The vault
   was clean afterwards — and since `add_note` writes the file *before* touching git, a hang in
   commit/push would have left the `.md` on disk. It didn't. Nothing got past validation.
2. `isError=True` delivery works: a `get_note` refusal (**structurally identical** — one text
   block, `structuredContent: null`) came back instantly in the same session.
3. The payload theories (the `tags` array, the ~1.5 KB body) died the same way: both return
   instantly.
4. **Approval is sticky** — a dialog appeared for `add_note` on its next call and *not* on the one
   after. A dialog appearing at all therefore proves `add_note` had **never** been approved before,
   including at 04:01. Combined with dispatch-is-gated (an approved call produces exactly **one**
   dispatch), it follows that **no `add_note` call ever reached the server**.

### The two traps, both worth remembering

**A hang at the client is not evidence of a hang at the server.** The client log
(`~/Library/Logs/Claude/mcp.log`) pairs every request with its response and timing — read it
*first*. Here it showed every call answered in ≤3 ms, which exonerated the server immediately.

**But that log does not record the tool name or the params** — only `method="tools/call" id=N
params { metadata: undefined }`. So two calls seen at 04:01 were assumed to be `add_note`, inferred
purely from the response *shape* (one content block). They were not `add_note` at all — almost
certainly the model obeying `add_note`'s own instructions to call `get_note_template` and
`list_vault` first, both of which return one block. That false identification produced a phantom
"the client auto-retried, so a response was lost" clue that was chased for some time.

**The generalisable failure — committed three times in one investigation, by three different
parties — is asserting a mechanism from a symptom without checking the premise it rests on.** The
fix is cheap and mechanical: before reasoning *from* a fact, verify the fact is recorded rather
than inferred. "Is that actually in the log, or did I derive it?" would have saved an hour.

### Client-side bugs (Claude Desktop — not ours, not actionable here)

Recorded so the next person doesn't re-derive them:

- The timeout message **blames the MCP server** ("unresponsive, crashed, or not running") for what
  is a client-side unanswered-approval timeout. Actively misleading.
- MCP call logging **omits the tool name and arguments**, which makes the logs nearly useless for
  attributing a call — the direct cause of the phantom-retry detour above.

## 2. Task #24 — the four hang vectors (this is the whole scope)

**None of these caused the reported symptom.** They were surfaced *by* the investigation and stand
on their own: each is a genuine way the server could hang or corrupt itself, and all are cheap to
close. This list is task #24 in full — the approval-dialog stall above needs no server change.

- [ ] **2a. `embedder.py` — `urlopen(req)` has no timeout.** Python defaults to *no limit*, so a
      stalled Ollama blocks **forever**. The realistic trigger is a **cold model load** on the
      first embed after boot. Anything that embeds is exposed: `search_second_brain`, and
      `git commit` itself (the pre-commit hook embeds the staged note). **This is the closest
      thing to a real unbounded hang in the system.** Fix: an explicit connect/read timeout, and
      a clear error saying Ollama did not respond — a slow brain must degrade to an error, never
      to silence.
- [ ] **2b. `mcp_server._git` inherits stdin — and stdin *is* the JSON-RPC channel.**
      `subprocess.run(..., capture_output=True)` redirects stdout/stderr but **not** stdin, so a
      git or ssh child can read from the protocol stream: it could consume Desktop's bytes and
      corrupt the session, or block waiting for input that never comes. Fix:
      `stdin=subprocess.DEVNULL` on every subprocess. A tool server must never let a child touch
      its transport.
- [ ] **2c. `GIT_TERMINAL_PROMPT=0` does not cover ssh.** It suppresses *git's* prompts, not
      **ssh's** passphrase or host-key prompts — and this brain's remote is SSH. Fix:
      `GIT_SSH_COMMAND="ssh -o BatchMode=yes"` so ssh fails instead of asking.
- [ ] **2d. `subprocess.TimeoutExpired` is not caught,** so a timeout surfaces as a traceback
      rather than a clean tool error. The 120 s per-call timeout is also long for a headless
      server. Fix: catch it, shorten the push timeout, and report it like any other failed push
      (the note is still committed and searchable — a failed push is not a lost note).

## 3. Tests to add (`tools/check_mcp_server.py`, write suite)

- [ ] `add_note` rejects every `para_root` outside `{projects, areas, resources, archive}` —
      including `"resources/test"`, `"resources/"`, `"../escape"`, and an absolute path.
- [ ] Rejection is **immediate and side-effect-free**: no file written, nothing staged, no commit,
      and it is bounded in wall-clock time (a validation error must not be able to take seconds).
- [ ] Every git step is **non-interactive** and **timeout-bounded**: no stdin is inherited, and no
      credential/passphrase prompt can block the call. Assert `stdin=DEVNULL` behaviourally by
      running against a remote that would otherwise prompt.
- [ ] An embed call that stalls **errors** rather than hanging (bound the embedder's timeout).

Every assertion is negative-tested, per the standing rule: a test that cannot be made to go red
is decoration.
