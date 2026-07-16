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

            # 1. exact tool surface (nine: #20 glossary pair, #5 write path, #25 add_glossary_term,
            #    #27 list_tags)
            expected = {"search_second_brain", "get_note",
                        "list_glossary_terms", "lookup_glossary_term",
                        "add_note", "list_vault", "get_note_template",
                        "add_glossary_term", "list_tags"}
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

            # 8. list tools filter, and cap HONESTLY — never truncate silently (#27) ------------
            if "list_tags" in tools:
                # the generated brain's seed notes carry frontmatter tags; list_tags surfaces the
                # vocabulary (nothing else does) sorted by count.
                tagrows = _json_blocks(await s.call_tool("list_tags", {}), fails, "list_tags")
                if not tagrows or not all("tag" in r and "count" in r for r in tagrows):
                    fails.append(f"list_tags did not return {{tag,count}} rows: {tagrows}")
                counts = [r["count"] for r in tagrows]
                if counts != sorted(counts, reverse=True):
                    fails.append(f"list_tags is not sorted by count desc: {tagrows}")
                # the match filter narrows to a substring
                one_tag = tagrows[0]["tag"]
                filtered = _json_blocks(await s.call_tool("list_tags", {"match": one_tag}),
                                        fails, "list_tags(match)")
                if any(one_tag not in r.get("tag", "") for r in filtered):
                    fails.append(f"list_tags(match={one_tag!r}) returned a non-matching tag: {filtered}")

            if "list_vault" in tools:
                # match filters note titles
                allres = _json_blocks(await s.call_tool(
                    "list_vault", {"para_root": "resources"}), fails, "list_vault(resources)")
                titles = [r.get("title", "") for r in allres if "title" in r]
                if titles:
                    probe = titles[0][:3]
                    got = _json_blocks(await s.call_tool(
                        "list_vault", {"para_root": "resources", "match": probe}),
                        fails, "list_vault(match)")
                    if any(probe.lower() not in r.get("title", "").lower()
                           for r in got if "title" in r):
                        fails.append(f"list_vault(match={probe!r}) returned a non-matching title")

            # a capped list must ANNOUNCE the truncation (a silent cap reads as "everything").
            # Re-run one tool under a cap of 1 via a second server, and require a _truncated marker.
            cap1 = {**env, "SECOND_BRAIN_LIST_CAP": "1"}
            params1 = StdioServerParameters(command=sys.executable, args=[server], env=cap1)
            async with stdio_client(params1) as (r1, w1):
                async with ClientSession(r1, w1) as s1:
                    await s1.initialize()
                    capped = _json_blocks(await s1.call_tool("list_tags", {}), fails,
                                          "list_tags (cap=1)")
                    if len(capped) != 2 or "_truncated" not in capped[-1]:
                        fails.append(f"a capped list did not announce the truncation (silent cap "
                                     f"reads as 'this is everything'): {capped}")
                    elif "of" not in capped[-1]["_truncated"] or "match" not in capped[-1]["_truncated"]:
                        fails.append(f"the truncation marker doesn't say how many/how to narrow: "
                                     f"{capped[-1]}")

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


def _git(brain: Path, *args: str, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=brain, env=env, capture_output=True, text=True)


def git_init_with_remote(brain: Path, bare: Path, env: dict) -> None:
    """Turn the generated brain into a real git repo with hooks + a bare remote.

    `generate()` (Mode A) emits files only — Mode B is what git-inits — but `add_note` commits
    and pushes, so the write path cannot be tested without a repo to commit *to*. A local bare
    repo stands in for the user's GitHub remote (same trick as `check_remote_sync.py`), which
    keeps the tier hermetic: no network, no credentials.
    """
    # Run the write suite with glossary_autolink ON — a NON-default config (#28). The bug this
    # guards against only exists when a pre-commit hook *edits* the staged note, and the only hook
    # that does is off by default. The suite passed for weeks against a config the user does not
    # run. A matrix that only covers defaults does not cover the product.
    cfg = brain / "config" / "features.toml"
    cfg.write_text(cfg.read_text(encoding="utf-8").replace("glossary_autolink = false",
                                                           "glossary_autolink = true"),
                   encoding="utf-8")
    _git(brain, "init", "-q", env=env)
    _git(brain, "config", "user.email", "mcp-check@example.invalid", env=env)
    _git(brain, "config", "user.name", "MCP Check", env=env)
    _git(brain, "config", "commit.gpgsign", "false", env=env)
    _git(brain, "config", "core.hooksPath", ".githooks", env=env)  # what embeds on commit
    subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True)
    _git(brain, "remote", "add", "origin", str(bare), env=env)
    _git(brain, "add", "-A", env=env)
    _git(brain, "commit", "-q", "-m", "seed brain", env=env)
    _git(brain, "push", "-q", "-u", "origin", "HEAD", env=env)


async def drive_write(brain: Path, bare: Path, env: dict) -> list[str]:
    """The #5 write path — `add_note` creates, commits, PUSHES, and is instantly searchable.

    This is the only tool that mutates the brain, so it gets the harshest tests. Two of them
    guard the user rather than the feature: `add_note` must never sweep a user's in-progress
    work into an agent-authored commit, and a traversal payload in the *title* must not escape
    the vault (the title is attacker-controlled text that becomes a filename).
    """
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server = str(brain / "scripts" / "mcp_server.py")
    params = StdioServerParameters(command=sys.executable, args=[server], env=env)
    fails: list[str] = []

    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as s:
            await s.initialize()

            # --- browse + template (how the model decides where a note belongs) -------------
            roots = _json_blocks(await s.call_tool("list_vault", {}), fails, "list_vault()")
            if {r.get("para_root") for r in roots} != {"projects", "areas", "resources", "archive"}:
                fails.append(f"list_vault() did not return the four PARA roots: {roots}")
            listed = _json_blocks(await s.call_tool("list_vault", {"para_root": "resources"}),
                                  fails, "list_vault(resources)")
            if not listed or not all("source_file" in n for n in listed):
                fails.append(f"list_vault(resources) returned no usable notes: {listed}")
            if not (await s.call_tool("list_vault", {"para_root": "glossary"})).isError:
                fails.append("list_vault accepted a non-PARA root ('glossary')")
            tpl = "".join(_texts(await s.call_tool("get_note_template", {})))
            if "tags:" not in tpl:
                fails.append(f"get_note_template did not return the vault template: {tpl[:80]!r}")
            # The editorial gate must REACH Claude Desktop. It lives in CLAUDE.md, which Desktop
            # never reads — the template is its only route. Without it an assistant can write a
            # mechanically perfect note about something utterly disposable, and add_note will
            # commit and push it: the tool makes filling the brain with junk fast and easy.
            if "would I search for this in six months" not in tpl:
                fails.append("get_note_template does not carry the 'what earns a note' gate — a "
                             "Desktop assistant has no bar for what deserves to be a note at all "
                             "(CLAUDE.md is invisible over MCP; the template is the only route)")

            # --- the happy path: create -> commit -> push -> searchable ---------------------
            # The body mentions a planted glossary term ("ablation"), so with glossary_autolink ON
            # the pre-commit hook EDITS this note and re-stages it — the exact condition that
            # exposed #28.
            res = await s.call_tool("add_note", {
                "title": "Write Path Check", "para_root": "resources",
                "body": "A note created over MCP by the harness, mentioning ablation once.",
                "tags": ["harness"]})
            report = " ".join(_texts(res))
            if res.isError:
                fails.append(f"add_note errored: {report[:160]}")
                return fails  # nothing below is meaningful if the write itself failed

            note = brain / "vault" / "resources" / "write-path-check.md"
            if not note.is_file():
                fails.append(f"add_note reported success but no note on disk: {note}")
            if not (note.parent / f".{note.stem}.embed.json").exists():
                fails.append("add_note committed but did not embed (the commit hook is what "
                             "embeds — this is the whole reason the tool commits)")
            if "pushed to origin" not in report:
                fails.append(f"add_note did not push: {report!r}")

            # --- #28: add_note must leave NO phantom staged change ---------------------------
            # A pathspec commit is a *partial* commit — git hands hooks a TEMPORARY index. With
            # glossary_autolink on, the hook edits the note and re-stages it into that temp index,
            # so the REAL index keeps the pre-hook blob: a staged REVERT of the hook's edit, which
            # the next commit by anyone silently applies (observed in the wild: an unrelated commit
            # un-linked [[ablation]] in a note it never touched). The index must match HEAD.
            staged_after = _git(brain, "diff", "--cached", "--name-only", env=env).stdout.strip()
            if staged_after:
                fails.append(f"add_note left a POISONED INDEX — staged after the call: "
                             f"{staged_after.split()} (a pathspec commit hides hook re-staging in "
                             f"a temp index; the real index must be re-synced)")
            # ...and the hook's edit really did survive into the commit (proves the hook ran at all,
            # so the assertion above isn't vacuously passing on a config where nothing edits).
            committed = _git(brain, "show", "HEAD:vault/resources/write-path-check.md",
                             env=env).stdout
            if "[[ablation]]" not in committed:
                fails.append("glossary_autolink did not link the term — the #28 index assertion "
                             "above is vacuous unless a hook actually edits the staged note")
            # the note is really in the REMOTE, not just locally committed
            remote_ls = subprocess.run(
                ["git", "--git-dir", str(bare), "ls-tree", "-r", "--name-only", "HEAD"],
                capture_output=True, text=True).stdout
            if "vault/resources/write-path-check.md" not in remote_ls:
                fails.append("the note never reached the remote — other clients would not see it")
            # ...and searchable immediately, which is the point of committing rather than writing
            hits = _json_blocks(await s.call_tool(
                "search_second_brain", {"query": "note created over MCP by the harness", "k": 5}),
                fails, "search (after add_note)")
            if not any("write-path-check.md" in h.get("source_file", "") for h in hits):
                fails.append("the new note is NOT searchable — add_note's core promise is broken")

            # --- refusals ------------------------------------------------------------------
            dup = await s.call_tool("add_note", {"title": "Write Path Check",
                                                 "para_root": "resources", "body": "again"})
            if not dup.isError:
                fails.append("add_note overwrote an existing note (it is create-only)")
            bad = await s.call_tool("add_note", {"title": "Nope", "para_root": "glossary",
                                                 "body": "x"})
            if not bad.isError:
                fails.append("add_note accepted a non-PARA root — a note could land anywhere")

            # --- traversal in the TITLE cannot escape the vault ----------------------------
            # The title is model/attacker-controlled text that becomes a filename. The slug is a
            # strict allow-list, so the payload collapses to a plain stem inside the chosen root
            # (it does not error — it sanitizes; what must never happen is a write outside).
            trav = await s.call_tool("add_note", {"title": "../../../etc/passwd",
                                                  "para_root": "resources", "body": "x"})
            if not trav.isError:
                created = " ".join(_texts(trav)).splitlines()[0].replace("created ", "").strip()
                landed = (brain / created).resolve()
                if (brain / "vault" / "resources").resolve() not in landed.parents:
                    fails.append(f"add_note ESCAPED the vault via the title: {landed}")
            if (brain.parent / "etc").exists() or (brain / "etc").exists():
                fails.append("add_note wrote outside the vault via a traversal title")

            # --- a dirty tree is never swept into the agent's commit -----------------------
            victim = brain / "vault" / "areas" / "knowledge-management.md"
            if victim.is_file():
                victim.write_text(victim.read_text(encoding="utf-8") + "\nuser work in progress\n",
                                  encoding="utf-8")
                _git(brain, "add", "--", "vault/areas/knowledge-management.md", env=env)
                r2 = await s.call_tool("add_note", {"title": "Dirty Tree Check",
                                                    "para_root": "resources", "body": "y"})
                if r2.isError:
                    fails.append(f"add_note failed with a dirty tree: {' '.join(_texts(r2))[:120]}")
                else:
                    touched = _git(brain, "show", "--stat", "--name-only", "--format=", "HEAD",
                                   env=env).stdout.split()
                    if touched != ["vault/resources/dirty-tree-check.md"]:
                        fails.append(f"add_note's commit swept up the user's work: {touched}")
                    staged = _git(brain, "diff", "--cached", "--name-only", env=env).stdout
                    if "knowledge-management.md" not in staged:
                        fails.append("add_note consumed the user's staged edit (it must be left "
                                     "staged and uncommitted)")
                _git(brain, "reset", "-q", "--", ".", env=env)
                _git(brain, "checkout", "-q", "--", "vault/areas/knowledge-management.md", env=env)

            # --- the multi-client case: the remote moved ahead, so rebase and retry ---------
            peer = brain.parent / "peer"
            subprocess.run(["git", "clone", "-q", str(bare), str(peer)], check=True)
            _git(peer, "config", "user.email", "peer@example.invalid", env=env)
            _git(peer, "config", "user.name", "Peer", env=env)
            (peer / "vault" / "resources" / "from-a-peer.md").write_text(
                "---\ntags: [peer]\n---\n\n# From A Peer\n\nWritten by another client.\n",
                encoding="utf-8")
            _git(peer, "add", "-A", env=env)
            _git(peer, "commit", "-q", "-m", "note: from a peer", env=env)
            _git(peer, "push", "-q", "origin", "HEAD", env=env)

            r3 = await s.call_tool("add_note", {"title": "After Peer Push",
                                                "para_root": "resources", "body": "z"})
            report3 = " ".join(_texts(r3))
            if "pushed to origin" not in report3:
                fails.append(f"add_note did not recover from a non-fast-forward push (the "
                             f"multi-client case): {report3!r}")

            # --- #25 add_glossary_term: define, LINK-cascade, commit, push (remote still live) --
            # A note that already mentions the term-to-be, so the sweep has something to link.
            host = brain / "vault" / "resources" / "glossary-host.md"
            host.write_text("---\ntags: [h]\n---\n\n# Host\n\nWe used beam search here.\n",
                            encoding="utf-8")
            _git(brain, "add", "--", "vault/resources/glossary-host.md", env=env)
            _git(brain, "commit", "-q", "-m", "note: glossary host", env=env)

            gres = await s.call_tool("add_glossary_term", {
                "term": "beam search",
                "definition": "A heuristic search keeping the k best partial candidates each step.",
                "aliases": ["beam-search decoding"]})
            greport = " ".join(_texts(gres))
            if gres.isError:
                fails.append(f"add_glossary_term errored: {greport[:160]}")
            else:
                gnote = brain / "vault" / "glossary" / "beam-search.md"
                if not gnote.is_file():
                    fails.append("add_glossary_term reported success but wrote no glossary note")
                # the definition was actually placed (the scaffold-substitution didn't silently
                # ship the placeholder)
                elif "k best partial candidates" not in gnote.read_text(encoding="utf-8"):
                    fails.append("add_glossary_term did not fill in the definition line")
                # the CASCADE: the pre-existing mention was linked, and committed in the SAME commit
                if "[[beam-search" not in host.read_text(encoding="utf-8"):
                    fails.append("add_glossary_term did not link the term into an existing note "
                                 "(the vault-wide sweep is the feature)")
                committed = _git(brain, "show", "--stat", "--name-only", "--format=", "HEAD",
                                 env=env).stdout.split()
                if "vault/glossary/beam-search.md" not in committed or \
                        "vault/resources/glossary-host.md" not in committed:
                    fails.append(f"the term note and the linked note did not land in one commit: "
                                 f"{committed}")
                # the glossary note must NOT be embedded (it is non-PARA — the exclusion holds)
                if (gnote.parent / f".{gnote.stem}.embed.json").exists():
                    fails.append("add_glossary_term embedded the glossary note — it must stay out "
                                 "of the vector index")
                # #28: no phantom staged change left behind
                if _git(brain, "diff", "--cached", "--name-only", env=env).stdout.strip():
                    fails.append("add_glossary_term left a poisoned index (staged after the call)")
                if "pushed to origin" not in greport:
                    fails.append(f"add_glossary_term did not push: {greport!r}")
                # reachable by lookup + alias, and ABSENT from search
                got = "".join(_texts(await s.call_tool(
                    "lookup_glossary_term", {"term": "beam-search decoding"})))
                if "k best partial candidates" not in got:
                    fails.append("the new term is not resolvable by its alias via lookup")
                sr = _json_blocks(await s.call_tool(
                    "search_second_brain", {"query": "beam search", "k": 5}), fails, "search(term)")
                if any("/glossary/" in h.get("source_file", "") for h in sr):
                    fails.append("the new glossary term leaked into search_second_brain")

            # duplicate term and alias-collision are refused
            dup = await s.call_tool("add_glossary_term",
                                    {"term": "Beam Search", "definition": "x"})
            if not dup.isError:
                fails.append("add_glossary_term redefined an existing term (must be create-only)")
            coll = await s.call_tool("add_glossary_term",
                                     {"term": "brand new term", "definition": "x",
                                      "aliases": ["beam-search decoding"]})
            if not coll.isError:
                fails.append("add_glossary_term accepted an alias that collides with an existing term")

            # --- an unpushable note must SHOUT, not whisper ---------------------------------
            # A failed push still returns SUCCESS (the note was created, committed, embedded), so
            # nothing makes the model mention it. If the warning isn't the FIRST thing in the
            # payload it gets summarized away as "saved!" and the user believes a note synced
            # when it didn't. Point the remote at a dead path to force the failure.
            _git(brain, "remote", "set-url", "origin", str(brain.parent / "gone.git"), env=env)
            r4 = await s.call_tool("add_note", {"title": "Unpushable Note",
                                                "para_root": "resources", "body": "w"})
            head = "".join(_texts(r4)).splitlines()[0] if _texts(r4) else ""
            if r4.isError:
                fails.append("add_note raised on a failed push — the note IS created, committed "
                             "and searchable, so this must be a partial success, not an error")
            elif "ACTION NEEDED" not in head or "NOT PUSHED" not in head:
                fails.append(f"a failed push is not surfaced on the FIRST line, so a model can "
                             f"summarize it away as 'saved': {head!r}")
            if not (brain / "vault" / "resources" / "unpushable-note.md").is_file():
                fails.append("add_note discarded the note when the push failed — a failed push "
                             "must never be a lost note")

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

        # The write path gets its OWN brain: add_note commits, pushes and mutates the vault, so
        # running it against the shared one would leave every read-side assertion above testing a
        # tree the writer had already changed. A third copy is cheaper than that coupling.
        wparent = Path(tempfile.mkdtemp(prefix="mcp-write-"))
        try:
            wbrain = wparent / "brain"
            shutil.copytree(brain, wbrain)
            git_init_with_remote(wbrain, wparent / "remote.git", env)
            print("git brain + bare remote -> write-path suite\n")
            fails += asyncio.run(drive_write(wbrain, wparent / "remote.git", env))
        finally:
            shutil.rmtree(wparent, ignore_errors=True)

        if fails:
            for f in fails:
                print(f"  FAIL  {f}")
            print(f"\nMCP tier FAILED: {len(fails)} assertion(s) regressed")
            return 1
        print("  ok    tools/list = the seven-tool surface (search, get_note, list_vault, "
              "get_note_template, the glossary pair, add_note)")
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
        print("  ok    add_note creates + commits + pushes to the remote, and the note is "
              "searchable at once (the commit is what embeds it)")
        print("  ok    add_note refuses a duplicate/non-PARA root, cannot escape the vault via "
              "the title, and never sweeps the user's staged work into its commit")
        print("  ok    add_note recovers from a non-fast-forward push (rebase + retry — the "
              "multi-client case)")
        print("  ok    list_vault browses the PARA roots; get_note_template returns the vault "
              "template")
        print("  ok    add_glossary_term defines + link-cascades + commits + pushes; term note "
              "not embedded; duplicate/alias-collision refused; excluded from search")
        print("\nMCP tier OK: server contract holds")
        return 0
    finally:
        shutil.rmtree(parent, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
