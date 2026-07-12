#!/usr/bin/env python3
"""G6 MCP tier — assert the MCP server *behaves*, not just that it's emitted (task #2).

`check_structural_diff.py` proves `scripts/mcp_server.py` is emitted byte-for-byte and
`ci.py`'s compile gate proves it parses — but neither *runs* it. This spawns the emitted
**stdio** server against a freshly generated `test`-backend brain and drives it with a
real MCP client, asserting the contract that matters to Claude Desktop:

  1. `tools/list` exposes exactly `search_second_brain` + `get_note`;
  2. **neither tool advertises an `outputSchema`** — older Claude Desktop MCP clients
     silently drop tools that do (the 2026-07-04 regression; docs/mcp-server.md §11);
  3. `get_note` refuses a path outside `vault/` (no arbitrary file reads);
  4. `search_second_brain` returns hits as **absolute** vault paths, and `get_note`
     reads one back.

**Opt-in and mcp-gated** — NOT part of the portable CI acceptance gate (which stays
stdlib-only). If the `mcp` SDK isn't installed it prints SKIP and exits 0. It uses the
deterministic `test` backend, so it needs **no Ollama**.

    python3 tools/check_mcp_server.py

This is a devkit tool; it is never emitted into a brain.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate import generate  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


def mcp_available() -> tuple[bool, str]:
    """(mcp SDK importable?, reason). Drives the SKIP gate — imported lazily so this
    file has no hard dependency on `mcp` (base requirements/CI stay stdlib-only)."""
    try:
        import mcp  # noqa: F401
        from mcp import ClientSession, StdioServerParameters  # noqa: F401
        from mcp.client.stdio import stdio_client  # noqa: F401
    except Exception as exc:  # noqa: BLE001 — any import failure means "not available"
        return False, f"mcp SDK not importable ({exc})"
    return True, ""


def _run(cmd: list[str], cwd: Path, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)


async def drive(brain: Path, env: dict) -> list[str]:
    """Drive the stdio server with an MCP client; return failures ([] == all passed)."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server = str(brain / "scripts" / "mcp_server.py")
    params = StdioServerParameters(command=sys.executable, args=[server], env=env)
    vault = str((brain / "vault").resolve())  # resolve: server resolves its own root
    fails: list[str] = []

    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as s:
            await s.initialize()
            tools = {t.name: t for t in (await s.list_tools()).tools}

            # 1. exact tool surface
            if set(tools) != {"search_second_brain", "get_note"}:
                fails.append(f"tools/list = {sorted(tools)}, "
                             "expected ['get_note', 'search_second_brain']")

            # 2. no outputSchema — the Claude Desktop compatibility lock
            for name, tool in tools.items():
                if getattr(tool, "outputSchema", None):
                    fails.append(f"{name} advertises an outputSchema — Claude Desktop "
                                 "would drop it (keep structured_output=False)")

            # 3/4. search returns absolute vault paths; get_note reads one back
            if "search_second_brain" in tools:
                res = await s.call_tool("search_second_brain",
                                        {"query": "knowledge management", "k": 3})
                if res.isError:
                    fails.append("search_second_brain call errored")
                else:
                    # structured_output=False → one text block per hit (JSON dict each)
                    hits = [json.loads(b.text) for b in res.content if hasattr(b, "text")]
                    if not hits:
                        fails.append("search_second_brain returned no hits")
                    for h in hits:
                        sf = h.get("source_file", "")
                        if not (os.path.isabs(sf) and sf.startswith(vault)):
                            fails.append(f"hit is not an absolute vault path: {sf!r}")
                        # hybrid search returns an RRF relevance score (higher = better)
                        if not isinstance(h.get("score"), (int, float)):
                            fails.append(f"hit missing numeric score: {h!r}")
                    if "get_note" in tools and hits:
                        note = await s.call_tool(
                            "get_note", {"source_file": hits[0]["source_file"]})
                        if note.isError or not note.content[0].text.strip():
                            fails.append("get_note returned empty/error for a real hit")

            # 3b. get_note refuses a path outside the vault
            if "get_note" in tools:
                bad = await s.call_tool("get_note", {"source_file": "/etc/passwd"})
                if not bad.isError:
                    fails.append("get_note did NOT refuse a path outside vault/")

    return fails


def main() -> int:
    ready, why = mcp_available()
    if not ready:
        print(f"SKIP MCP tier — {why}")
        print("  (opt-in, mcp-gated; not part of the CI acceptance gate)")
        return 0

    env = {**os.environ, "SECOND_BRAIN_EMBEDDER": "test"}  # deterministic, no Ollama
    parent = Path(tempfile.mkdtemp(prefix="mcp-check-"))
    brain = parent / "brain"
    try:
        generate(brain)
        print(f"generated brain -> {brain}")
        # test backend: embed + hydrate so the server has a cache to search (no Ollama).
        if _run([sys.executable, "scripts/embed_vault.py"], brain, env).returncode != 0:
            raise SystemExit("mcp: embed_vault.py failed")
        if _run([sys.executable, "scripts/hydrate_cache.py"], brain, env).returncode != 0:
            raise SystemExit("mcp: hydrate_cache.py failed")
        print("embedded + hydrated (test backend)\n")

        fails = asyncio.run(drive(brain, env))
        if fails:
            for f in fails:
                print(f"  FAIL  {f}")
            print(f"\nMCP tier FAILED: {len(fails)} assertion(s) regressed")
            return 1
        print("  ok    tools/list = [get_note, search_second_brain]")
        print("  ok    no outputSchema on either tool (Claude Desktop-safe)")
        print("  ok    search returns absolute vault paths; get_note reads a hit")
        print("  ok    get_note refuses paths outside vault/")
        print("\nMCP tier OK: server contract holds")
        return 0
    finally:
        shutil.rmtree(parent, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
