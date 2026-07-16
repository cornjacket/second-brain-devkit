#!/usr/bin/env python3
"""Gate 12 — nothing the server does can hang forever (task #24).

Four ways the emitted server could hang or corrupt itself, none hypothetical:

  1. **The embedder's HTTP call had no timeout** — a stalled Ollama (typically a cold model load)
     would block the caller *forever*, and the caller may be the long-lived MCP server, so one bad
     embed freezes every tool. The unbounded hang.
  2. **`_git` inherited stdin** — but on stdio the server's stdin IS the JSON-RPC channel, so a git
     or ssh child could read protocol bytes and corrupt the session (`stdin=DEVNULL`).
  3. **`GIT_TERMINAL_PROMPT=0` doesn't cover ssh** — ssh's own passphrase/host-key prompt would
     hang a push on input that can never come (`GIT_SSH_COMMAND=ssh -o BatchMode=yes`).
  4. **A subprocess timeout surfaced as a traceback** instead of a clean failed-op report.

(1) is tested **behaviorally** — hermetically, against a local socket that accepts a connection and
never answers (a real "accepts but hangs" server, no external network) — because a bug here is a
*runtime* hang no amount of source-reading proves absent. (2)-(4) are pinned **statically** on the
emitted `_git`, since they are guarantees about how the subprocess is spawned.

    python3 tools/check_hang_safety.py

Hermetic; stdlib only. Devkit tool, never emitted.
"""
from __future__ import annotations

import os
import socket
import sys
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EMITTED = REPO_ROOT / "template" / "scripts"


def _blackhole() -> tuple[str, socket.socket]:
    """A listening socket that accepts a connection and then never sends a byte. The faithful
    'server is up but wedged' case — the one an unbounded urlopen waits on forever."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)

    def _accept_and_stall():
        try:
            conn, _ = srv.accept()
            time.sleep(30)      # hold it open, answer nothing
            conn.close()
        except OSError:
            pass

    threading.Thread(target=_accept_and_stall, daemon=True).start()
    return f"http://127.0.0.1:{srv.getsockname()[1]}", srv


def check_embed_timeout() -> list[str]:
    """The emitted embedder must ERROR within a bound against a wedged Ollama, not hang.

    The embed runs in a daemon thread that this function joins with its OWN bound — so if the
    embedder hangs (the bug), the *gate* reports it as a failure rather than hanging CI. A gate
    that can hang is worse than the bug it guards.
    """
    sys.path.insert(0, str(EMITTED))
    host, srv = _blackhole()
    result: dict = {}

    def _do():
        old = dict(os.environ)
        os.environ.update({"SECOND_BRAIN_EMBEDDER": "ollama", "OLLAMA_HOST": host,
                           "SECOND_BRAIN_EMBED_TIMEOUT": "2"})
        try:
            import importlib
            import embedder
            importlib.reload(embedder)  # pick up the env
            try:
                embedder.embed("probe", task="document")
                result["outcome"] = "returned"
            except Exception as exc:  # noqa: BLE001 — a bounded error is a pass; a hang is the fail
                result["outcome"] = "raised"
                result["msg"] = str(exc)
        finally:
            os.environ.clear()
            os.environ.update(old)

    try:
        th = threading.Thread(target=_do, daemon=True)
        t0 = time.time()
        th.start()
        th.join(timeout=8)  # the embedder's own timeout is 2s; 8s is generous headroom
        dt = time.time() - t0
        if th.is_alive():
            return [f"embedder did NOT return within {dt:.0f}s against a wedged Ollama — its HTTP "
                    "call is unbounded (a cold/stalled Ollama would freeze the server forever)"]
        if result.get("outcome") == "returned":
            return ["embedder returned from a wedged Ollama — impossible unless the timeout was "
                    "removed (or the black-hole failed to bind)"]
        if "did not respond" not in result.get("msg", ""):
            return [f"embedder failed, but not with the timeout error — got: "
                    f"{result.get('msg', '')[:100]}"]
        return []
    finally:
        srv.close()


def check_git_guards() -> list[str]:
    """Static guarantees on the emitted `_git` — how the git subprocess is spawned."""
    src = (EMITTED / "mcp_server.py").read_text(encoding="utf-8")
    # isolate the _git function body so we assert on IT, not on some other subprocess call
    start = src.find("def _git(")
    if start == -1:
        return ["mcp_server.py has no _git() — the git wrapper the guards live on is gone"]
    end = src.find("\ndef ", start + 1)
    body = src[start:end if end != -1 else len(src)]

    required = {
        "stdin=subprocess.DEVNULL": "a git/ssh child could read the JSON-RPC stdin channel",
        "BatchMode=yes": "ssh could prompt for a passphrase/host-key and hang the push",
        "GIT_TERMINAL_PROMPT": "git could prompt for credentials and hang",
        "timeout": "no ceiling on a wedged git op",
        "TimeoutExpired": "a timeout would surface as a traceback, not a clean failure",
    }
    fails = []
    for token, why in required.items():
        if token not in body:
            fails.append(f"_git() is missing {token!r} — {why}")
    return fails


def main() -> int:
    fails = check_embed_timeout() + check_git_guards()
    if fails:
        for f in fails:
            print(f"  FAIL  {f}")
        print(f"\nhang-safety FAILED: {len(fails)} assertion(s)")
        return 1
    print("  ok    embedder errors within a bound against a wedged Ollama (no unbounded hang)")
    print("  ok    _git spawns with DEVNULL stdin, ssh BatchMode, git prompt off, a timeout, and "
          "catches TimeoutExpired")
    print("\nhang-safety OK: no unbounded wait reachable from the server")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
