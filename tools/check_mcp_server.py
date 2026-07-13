#!/usr/bin/env python3
"""G6 MCP tier — assert the MCP server *behaves*, not just that it's emitted (task #2).

`check_structural_diff.py` proves `scripts/mcp_server.py` is emitted byte-for-byte and
`ci.py`'s compile gate proves it parses — but neither *runs* it. This spawns the emitted
**stdio** server against a freshly generated `test`-backend brain and drives it with a
real MCP client, asserting the contract that matters to Claude Desktop:

  1. `tools/list` exposes exactly the four tools — `search_second_brain`, `get_note`,
     and the #20 glossary pair `list_glossary_terms` + `lookup_glossary_term`;
  2. **no tool advertises an `outputSchema`** — older Claude Desktop MCP clients
     silently drop tools that do (the 2026-07-04 regression; docs/mcp-server.md §11);
  3. `get_note` refuses a path outside `vault/` (no arbitrary file reads);
  4. `search_second_brain` returns hits as **absolute** vault paths, and `get_note`
     reads one back;
  5. the glossary tools (#20) list a planted term, resolve it by exact key / alias /
     normalized phrasing, return a near-miss on a typo, stay **excluded** from
     `search_second_brain`, and pick up a newly-added term without a restart.

Task #21 adds the failure modes — what the server must *refuse* or *survive*:

  6. **Path traversal.** `get_note` takes a caller-supplied path, so it is the one
     untrusted-input surface. Every escape is refused *as an escape* (not merely as a
     missing file), including escapes to real files; and a `..` that stays **inside**
     the vault is still served — proving the guard is resolve-based escape detection,
     not a naive `..`-string reject.
  7. **Substrate disjointness.** Search returns only PARA notes; the glossary tools
     return only glossary notes. The two retrieval substrates never overlap.
  8. **The glossary is embedding-free.** A second server is driven against a brain with
     the vector substrate *removed* (`data/` deleted, every `.embed.json` sidecar gone):
     search comes back empty, yet the glossary tools still answer — they can only be
     reading `vault/glossary/*.md`, never `data/brain.db`.

Known gap (out of scope): a **symlink** inside `vault/` pointing out would resolve out
and so be refused by the same guard, but nothing in a brain ever creates one, so it is
not exercised here.

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


def _texts(res) -> list[str]:
    """Text blocks of a tool result — structured_output=False, so every payload (and every
    error message) comes back as text."""
    return [b.text for b in res.content if hasattr(b, "text")]


def _slug(term: str) -> str:
    """Term display name -> the filename stem it must have come from."""
    return term.strip().lower().replace(" ", "-")


def _json_blocks(res, fails: list[str], label: str) -> list[dict]:
    """Parse a tool's JSON text blocks defensively. A tool that errored (or answered with a
    bare error string instead of JSON) is a reported FAIL — never a traceback: a regression
    must fail this tier *legibly*, or the next person reads a stack trace instead of a cause."""
    if res.isError:
        fails.append(f"{label} errored: {' '.join(_texts(res)).strip()[:120]}")
        return []
    out: list[dict] = []
    for t in _texts(res):
        try:
            out.append(json.loads(t))
        except json.JSONDecodeError:
            fails.append(f"{label} returned non-JSON: {t.strip()[:120]!r}")
    return out


async def drive(brain: Path, env: dict) -> list[str]:
    """Drive the stdio server with an MCP client; return failures ([] == all passed)."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server = str(brain / "scripts" / "mcp_server.py")
    params = StdioServerParameters(command=sys.executable, args=[server], env=env)
    vault = str((brain / "vault").resolve())  # resolve: server resolves its own root
    fails: list[str] = []
    hits: list[dict] = []

    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as s:
            await s.initialize()
            tools = {t.name: t for t in (await s.list_tools()).tools}

            # 1. exact tool surface (four tools since #20 added the glossary pair)
            expected = {"search_second_brain", "get_note",
                        "list_glossary_terms", "lookup_glossary_term"}
            if set(tools) != expected:
                fails.append(f"tools/list = {sorted(tools)}, expected {sorted(expected)}")

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
                    hits = _json_blocks(res, fails, "search_second_brain")
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

            # 3b/6. path traversal — get_note is the only untrusted-input surface (task #21).
            #    The guard resolves the path first, then requires vault/ among its parents, so
            #    `..` is collapsed BEFORE the check. Assert BOTH halves of that:
            #    (a) every escape is refused — including escapes to files that really exist, and
            #        the message must be the vault refusal, not an incidental FileNotFoundError
            #        (a not-found would "pass" a naive test while proving nothing about the guard);
            #    (b) a `..` that stays inside the vault is still SERVED — so we know the guard
            #        detects escapes rather than blanket-rejecting the string "..".
            #    Relative paths resolve against the brain root, not vault/, so a bare
            #    `config/...` is already an escape.
            if "get_note" in tools:
                escapes = [
                    "/etc/passwd",                    # absolute, far outside the brain
                    "vault/../README.md",             # `..` escape to a real file in the brain
                    "vault/../config/embedder.toml",  # hop to a real sibling of vault/
                    "config/embedder.toml",           # relative == brain-root-relative, not vault
                    "../../etc/passwd",               # climb out of the brain entirely
                ]
                for bad in escapes:
                    r = await s.call_tool("get_note", {"source_file": bad})
                    if not r.isError:
                        fails.append(f"get_note({bad!r}) was NOT refused — arbitrary file read")
                    elif "refusing to read outside the vault" not in " ".join(_texts(r)):
                        fails.append(f"get_note({bad!r}) failed, but not on the vault guard: "
                                     f"{' '.join(_texts(r)).strip()[:90]!r}")
                if hits:  # (b) the in-vault `..` round-trip: <dir>/../<dir>/<note>.md
                    hit = Path(hits[0]["source_file"])
                    inside = str(hit.parent / ".." / hit.parent.name / hit.name)
                    ok = await s.call_tool("get_note", {"source_file": inside})
                    if ok.isError or not "".join(_texts(ok)).strip():
                        fails.append(f"get_note refused an in-vault `..` path (the guard is a "
                                     f"naive '..' reject, not escape detection): {inside}")

            # 5. glossary tools (#20) — exact-match symbolic layer, no embeddings.
            #    main() planted vault/glossary/ablation.md (aliases: ablation study, ablations).
            listed: list[dict] = []
            listed2: list[dict] = []
            if "list_glossary_terms" in tools:
                listed = _json_blocks(await s.call_tool("list_glossary_terms", {}),
                                      fails, "list_glossary_terms")
                if "ablation" not in {e.get("term") for e in listed}:
                    fails.append(f"list_glossary_terms missing 'ablation': {listed}")

            if "lookup_glossary_term" in tools:
                # exact, alias, and normalized ("Ablation Study?") all resolve to the note
                for q in ("ablation", "ablations", "Ablation Study?"):
                    got = "".join(_texts(await s.call_tool("lookup_glossary_term", {"term": q})))
                    if "measure its contribution" not in got:
                        fails.append(f"lookup_glossary_term({q!r}) did not return the note")
                # a typo returns a near-miss suggestion, not a bare not-found
                miss = "".join(_texts(await s.call_tool(
                    "lookup_glossary_term", {"term": "ablasion"})))
                if "measure its contribution" in miss or "ablation" not in miss:
                    fails.append("lookup_glossary_term('ablasion') gave no near-miss suggestion")

            # 5b. search still EXCLUDES the glossary (embedding-exclusion holds at the tool)
            if "search_second_brain" in tools:
                gl = _json_blocks(await s.call_tool(
                    "search_second_brain", {"query": "ablation", "k": 5}), fails, "search(ablation)")
                if any("/glossary/" in h.get("source_file", "") for h in gl):
                    fails.append("search_second_brain returned a glossary note (exclusion breached)")

            # 5c. a newly-added term is listable WITHOUT a server restart (mtime-cached index)
            if "list_glossary_terms" in tools:
                (brain / "vault" / "glossary" / "corpus.md").write_text(
                    "---\ntype: glossary\n---\n\n# corpus\n\nA labeled note collection.\n",
                    encoding="utf-8")
                listed2 = _json_blocks(await s.call_tool("list_glossary_terms", {}),
                                       fails, "list_glossary_terms (after hot-add)")
                if "corpus" not in {e.get("term") for e in listed2}:
                    fails.append("newly-added glossary term not listable without a restart")

            # 7. substrate disjointness (task #21) — the two retrieval paths never overlap.
            #    Search side: every hit is a PARA note (5b already proved no glossary/ path;
            #    this proves the positive — hits come from the four PARA roots and nowhere else).
            para = ("/projects/", "/areas/", "/resources/", "/archive/")
            for h in hits:
                sf = h.get("source_file", "")
                if not any(root in sf for root in para):
                    fails.append(f"search hit is not a PARA note: {sf!r}")
            #    Glossary side: every listed term is backed by a file in vault/glossary/ — no
            #    PARA note can leak in (the server skips README.md/_-prefixed, so must we).
            if "list_glossary_terms" in tools:
                on_disk = {p.stem for p in (brain / "vault" / "glossary").glob("*.md")
                           if p.name != "README.md" and not p.name.startswith("_")}
                leaked = {e["term"] for e in listed2 if _slug(e["term"]) not in on_disk}
                if leaked:
                    fails.append(f"list_glossary_terms returned non-glossary terms: {leaked}")
            #    ...and a lookup returns the glossary note itself, not a PARA note about it.
            if "lookup_glossary_term" in tools:
                got = "".join(_texts(await s.call_tool(
                    "lookup_glossary_term", {"term": "ablation"})))
                if "type: glossary" not in got:
                    fails.append("lookup_glossary_term returned a non-glossary note")

    return fails


async def drive_novectors(brain: Path, env: dict) -> list[str]:
    """The glossary is embedding-free (task #21) — assert it against a brain whose vector
    substrate is gone: every `.embed.json` sidecar deleted and `data/brain.db` **poisoned**
    with garbage bytes.

    Poisoned, not deleted, and that distinction is the whole test: the server *rebuilds* a
    missing cache on startup (`main()` hydrates when `DB_PATH` is absent), so a merely-deleted
    db is back — empty but valid — before the first tool call, and a glossary that secretly
    read it would still pass. A corrupt db cannot be opened at all, so **any** read of the
    vector cache on the glossary path raises. Search is expected to fail or come back empty
    here; the glossary must still answer in full, which it can only do by reading
    `vault/glossary/*.md` directly.

    Pair this with `check_glossary_is_db_free()` — behavioral proof that the glossary never
    *reads* the cache, static proof that it never *names* it.
    """
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server = str(brain / "scripts" / "mcp_server.py")
    params = StdioServerParameters(command=sys.executable, args=[server], env=env)
    fails: list[str] = []

    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as s:
            await s.initialize()

            # Sanity-check the setup itself: if search still worked, the substrate was not
            # really stripped and every glossary assertion below would be vacuous.
            res = await s.call_tool("search_second_brain", {"query": "ablation", "k": 5})
            # search is EXPECTED to fail here (the db is garbage) — an error is the healthy
            # outcome, so don't route it through _json_blocks, which would report it as a FAIL.
            hits = [] if res.isError else [t for t in _texts(res) if t.strip()]
            if hits:
                fails.append(f"vector-free brain still returned {len(hits)} search hit(s) — "
                             "the substrate was not actually destroyed, so this proves nothing")

            listed = _json_blocks(await s.call_tool("list_glossary_terms", {}),
                                  fails, "list_glossary_terms (vector-free brain)")
            if "ablation" not in {e.get("term") for e in listed}:
                fails.append(f"list_glossary_terms broke without vectors: {listed}")

            got = "".join(_texts(await s.call_tool("lookup_glossary_term", {"term": "ablations"})))
            if "measure its contribution" not in got:
                fails.append("lookup_glossary_term broke without vectors — it depends on brain.db")

    return fails


def check_glossary_is_db_free(brain: Path) -> list[str]:
    """Static half of the embedding-free proof (task #21): the glossary code path must not so
    much as *name* the vector substrate.

    The behavioral test (`drive_novectors`) catches a glossary that *reads* `brain.db`. This
    catches the subtler coupling it cannot see — e.g. gating the glossary on
    `DB_PATH.exists()`, which changes behavior without ever opening the file. Together they
    pin the invariant that keeps the two substrates independent: the glossary is reachable in
    a brain that has never embedded anything.
    """
    import ast

    src = (brain / "scripts" / "mcp_server.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    forbidden = ("DB_PATH", "brain.db", "search_vault", "hydrate_cache", "embedder")
    glossary_fns = {"_glossary_index", "list_glossary_terms", "lookup_glossary_term"}
    fails: list[str] = []

    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in glossary_fns:
            found.add(node.name)
            body = ast.get_source_segment(src, node) or ""
            for token in forbidden:
                if token in body:
                    fails.append(f"{node.name}() references {token!r} — the glossary must not "
                                 "touch the vector substrate (embedding-free by contract)")
    if found != glossary_fns:
        fails.append(f"glossary functions not found in mcp_server.py: {glossary_fns - found}")
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
        # Plant a glossary term (#20 coverage) — a brain ships an empty glossary. It must NOT
        # be embedded (glossary/ is non-PARA), so the embed pass below should ignore it.
        (brain / "vault" / "glossary" / "ablation.md").write_text(
            "---\ntype: glossary\naliases: [ablation study, ablations]\ntags: [glossary]\n---\n\n"
            "# ablation\n\nTurning one feature off to measure its contribution.\n",
            encoding="utf-8")
        # test backend: embed + hydrate so the server has a cache to search (no Ollama).
        if _run([sys.executable, "scripts/embed_vault.py"], brain, env).returncode != 0:
            raise SystemExit("mcp: embed_vault.py failed")
        if _run([sys.executable, "scripts/hydrate_cache.py"], brain, env).returncode != 0:
            raise SystemExit("mcp: hydrate_cache.py failed")
        print("embedded + hydrated (test backend)\n")

        fails = asyncio.run(drive(brain, env))

        # A second brain with the vector substrate destroyed — the glossary must survive it.
        # Copied AFTER drive(), so it also carries the `corpus` term drive() hot-added.
        # brain.db is POISONED, not deleted: the server re-hydrates a missing cache on startup,
        # so deleting it would hand the glossary a valid (empty) db and prove nothing. Garbage
        # bytes exist (no re-hydrate) but cannot be opened — any read of it now raises.
        novec = parent / "novec"
        shutil.copytree(brain, novec)
        for sidecar in (novec / "vault").rglob("*.embed.json"):
            sidecar.unlink()
        (novec / "data" / "brain.db").write_bytes(b"not a sqlite database\n")
        for wal in (novec / "data").glob("brain.db-*"):  # stale WAL/shm would mask the poison
            wal.unlink()
        print("destroyed vectors (sidecars deleted + brain.db poisoned) -> novec brain\n")
        fails += asyncio.run(drive_novectors(novec, env))
        fails += check_glossary_is_db_free(brain)

        if fails:
            for f in fails:
                print(f"  FAIL  {f}")
            print(f"\nMCP tier FAILED: {len(fails)} assertion(s) regressed")
            return 1
        print("  ok    tools/list = [get_note, list_glossary_terms, lookup_glossary_term, "
              "search_second_brain]")
        print("  ok    no outputSchema on any tool (Claude Desktop-safe)")
        print("  ok    search returns absolute vault paths; get_note reads a hit")
        print("  ok    glossary: list includes 'ablation'; lookup resolves exact/alias/normalized")
        print("  ok    glossary: typo returns a near-miss; search excludes glossary; new term "
              "listable without restart")
        print("  ok    get_note refuses every escape (absolute, .. out, real sibling) on the "
              "vault guard; an in-vault `..` still reads")
        print("  ok    substrates disjoint: search returns only PARA notes, glossary tools only "
              "glossary notes")
        print("  ok    glossary answers with the vector substrate destroyed, and never names it "
              "(embedding-free: no read of brain.db, no reference to it)")
        print("\nMCP tier OK: server contract holds")
        return 0
    finally:
        shutil.rmtree(parent, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
