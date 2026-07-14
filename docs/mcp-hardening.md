# MCP server hardening — nothing may hang the server (task #24)

**Status:** OPEN (surfaced 2026-07-14, from a Claude Desktop bug report).
**Scope:** the emitted `scripts/mcp_server.py` and `scripts/embedder.py`.
**Constraint that does not bend:** none of this touches the indexer's walk. `glossary/` and
`templates/` are excluded from the vector index *purely* by not being PARA roots — no exclusion
list, no config flag — and that must hold. Every fix below is inside the tool/subprocess layer.

---

## 1. What was reported, and what was actually true

**Report:** `add_note` hangs (no response, 4-minute client timeout) when `para_root` contains a
path separator (`"resources/test"`). Suspected cause: it gets past validation and blocks in the
`git push`.

**Finding: the server never hung, and the reported cause does not exist.** Claude Desktop's own
client log is decisive — *every* call was answered, and none took longer than **3 ms**:

```
04:01:38.569  client → tools/call  id=7
04:01:38.571  server → result        (2 ms)
04:01:42.501  client → tools/call  id=8
04:01:42.504  server → result        (3 ms)
```

Corroborating evidence:

- `para_root` **is** validated: `if para_root not in PARA_ROOTS: raise ValueError(...)` — a strict
  membership test against the 4-tuple, not a path join. Reproduced under Desktop's own minimal
  launchd environment (no `SSH_AUTH_SOCK`): **returns in 0.00 s, `isError=True`, no side effects.**
- The **vault was clean** afterwards — nothing written, staged, or committed. `add_note` writes the
  file *before* it touches git, so a hang in commit/push would have left the `.md` on disk. It
  didn't, which proves nothing ever got past validation.
- The push does **not** block in that environment either: it fails fast (0.83 s, `publickey`).
- Sampling the live server process showed it **idle** in its event loop, not stuck.

The stall was therefore **client-side in Claude Desktop, after the server had already answered**.
Not a server bug. Recorded here so nobody "fixes" the validation twice.

**The lesson worth keeping:** a hang reported at the client is not evidence of a hang at the
server. The MCP client log (`~/Library/Logs/Claude/mcp.log`) pairs every request with its
response and timing — read it *first*, before theorising about the server.

## 2. The real defects the investigation surfaced

None of these caused the reported symptom. All are genuine ways the server **could** hang or
corrupt itself, and all are cheap to close.

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
