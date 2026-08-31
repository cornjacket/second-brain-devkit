#!/usr/bin/env python3
"""Gate 23 — a note and its material live together, and neither corrupts the other.

The goal this closes: write a Markdown note **and an accompanying `.svg`** into a nested
project folder. Three separate mechanisms have to hold at once, and each fails differently.

**1. Nesting is allowed where it is motivated, and refused where it is not.** `subpath` works
under `projects/` and `archive/` only. A project is goal-bound and ends, so its note and its
material want to archive or delete as one unit — that motive is the entire reason to nest. A
resource is filed by topic and an area never ends, so nesting there buries notes for no gain.
Both roots refuse, loudly.

**2. An asset is never embedded, and its filename never reaches a vector.** Only Markdown is
eligible to embed — that is structural (every walker globs `*.md`), not a flag. But the
*reference* is a second leak: left alone, `![alt](tile-pattern.svg)` puts `tile-pattern.svg`
into the note's embedding, and notes start resembling each other by how their files are named
rather than by what they say. The filename goes; the human-written alt text stays, because it
is often the only description of the picture the embedder will ever see.

**3. Filename uniqueness is now enforced, not assumed.** Obsidian resolves `[[wikilinks]]` by
**basename**. That was globally unique by accident — notes sat in a flat root, and a directory
cannot hold two files of one name — and subfolders remove the accident *silently*, because two
nested notes of the same name are two valid, different paths that every prior check accepts. A
property held up by how things happen to be arranged is not an invariant; this gate exists
because the pre-commit hook now makes it one.

Also pinned: `add_asset` refuses an **orphan** (no note in the folder — nothing would embed it,
link it, or return it, so it is invisible the moment you forget it is there), and refuses
outright on an **encrypted** brain, where the vault is git-ignored and only `*.md` is
encrypted, so the file would reach no commit in any form (task #49). Refusing beats reporting
a success that pushed nothing.

Hermetic: stdlib + git + sqlite-vec, deterministic ``test`` backend, no Ollama, no network.
The MCP tools are exercised by direct import, not over stdio — the ``mcp`` SDK is optional and
CI does not install it, so this imports the module and calls the functions the decorator wraps.

    python3 tools/check_asset_colocation.py

Devkit tool; never emitted.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN = REPO_ROOT / "tests" / "golden"
PY = sys.executable

sys.path.insert(0, str(REPO_ROOT / "tools"))
from generate import generate  # noqa: E402

SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60">'
       '<rect width="60" height="60" fill="#eee"/></svg>\n')


def _run(argv: list[str], cwd: Path, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run([argv[0], "-B", *argv[1:]], cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=600)


def _git(brain: Path, *args: str, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=brain, env=env,
                          capture_output=True, text=True, timeout=120)


def _setup(brain: Path, env: dict) -> None:
    generate(brain)
    _git(brain, "init", "-q", env=env)
    _git(brain, "config", "user.email", "asset@example.invalid", env=env)
    _git(brain, "config", "user.name", "Asset Check", env=env)
    _git(brain, "config", "commit.gpgsign", "false", env=env)
    _git(brain, "config", "core.hooksPath", ".githooks", env=env)
    _git(brain, "add", "-A", env=env)
    _git(brain, "commit", "-q", "-m", "seed brain", env=env)
    for script in ("embed_vault.py", "hydrate_cache.py"):
        r = _run([PY, f"scripts/{script}"], brain, env)
        if r.returncode != 0:
            raise SystemExit(f"asset-colocation: {script} failed: {(r.stderr or r.stdout)[-300:]}")


def check_projection(fails: list[str]) -> None:
    """The canonical view, asserted against the vendored module (no brain needed)."""
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(GOLDEN / "scripts"))
    try:
        import note_view as nv
    except ImportError as exc:
        fails.append(f"cannot import the vendored note_view: {exc}")
        return

    def view(body: str) -> str:
        return nv.canonical_body(f"---\ntags: [t]\n---\n\n# N\n\n{body}\n")

    v = view("![a tiling of the plane](tile-pattern.svg)")
    if "tile-pattern.svg" in v:
        fails.append("an asset FILENAME reached the embed input — every note showing a diagram "
                     "would carry its filename in the vector")
    if "a tiling of the plane" not in v:
        fails.append("the alt text was dropped from the embed input — it is the human-written "
                     "description of the picture, often the only one the embedder ever sees")
    if "tile-pattern" in view("![[tile-pattern.svg]]"):
        fails.append("an Obsidian ![[asset]] embed left its filename in the embed input")
    if "algebra" not in view("See [[algebra]]."):
        fails.append("a wikilink to another NOTE was mangled — only assets should be stripped")
    if "https://example.com/a.html" not in view("See [docs](https://example.com/a.html)."):
        fails.append("an external URL was rewritten — it is a source the note cites, not an "
                     "asset in this vault")

    suite = GOLDEN / "tests" / "test_asset_colocation.py"
    if not suite.is_file():
        fails.append("vendored tests/test_asset_colocation.py missing (run vendor_golden.py)")
    elif subprocess.run([PY, "-B", str(suite)], capture_output=True, text=True).returncode != 0:
        fails.append("the emitted asset/uniqueness suite regressed")


def check_payload(brain: Path, env: dict, fails: list[str]) -> None:
    """The real thing: two nested notes plus a sibling SVG, through the MCP tools."""
    sys.path.insert(0, str(brain / "scripts"))
    for stale in ("mcp_server", "note_view", "features", "db", "search_vault", "add_pdf"):
        sys.modules.pop(stale, None)
    cwd = os.getcwd()
    os.chdir(brain)
    try:
        import mcp_server as m
    except ImportError as exc:
        print(f"        optional 'mcp' SDK absent — the tool surface was NOT exercised ({exc})")
        os.chdir(cwd)
        return
    try:
        # Built the way the docs say to build it: structure via entry=, never in the title.
        # The titles here are deliberately plain headings — "Chapter 1", not
        # "Algebra 1--Chapter 1" — which is the readability the decoupling buys.
        #
        # Wrapped: a regression here raises rather than returning, and an unhandled traceback
        # is a worse failure report than a named assertion. It also stops the rest of the gate
        # running, so one break hides every other result.
        try:
            m.add_note("Algebra 1", "projects", "The algebra project.", ["math"],
                       subpath="algebra-1", entry=True)
            m.add_note("Chapter 1", "projects",
                       "Tessellation of the plane.\n\n![a tiling](tile-pattern-cpm-source.svg)",
                       ["math"], subpath="algebra-1/algebra-1--chapter-1", entry=True)
            m.add_note("Worked Solutions", "projects", "The answers.", ["math"],
                       subpath="algebra-1/algebra-1--chapter-1", descriptor="worked-solutions")
            m.add_asset("projects", "algebra-1/algebra-1--chapter-1",
                        "tile-pattern-cpm-source.svg", SVG)
        except Exception as exc:
            fails.append(f"building the documented payload FAILED — the example in the docs "
                         f"cannot be executed: {type(exc).__name__}: {str(exc)[:220]}")
            return

        base = "vault/projects/algebra-1/algebra-1--chapter-1"
        svg = brain / base / "tile-pattern-cpm-source.svg"
        note = brain / base / "algebra-1--chapter-1.md"
        if not (brain / base / "algebra-1--chapter-1--worked-solutions.md").is_file():
            fails.append("descriptor= did not scope the filename under its folder — the `--` "
                         "join was collapsed, which is the bug the parameter exists to avoid")
        if note.is_file() and "# Chapter 1" not in note.read_text(encoding="utf-8"):
            fails.append("the H1 is not the title — entry= is supposed to free the heading "
                         "from the filename, which is half the reason it exists")
        if not svg.is_file():
            fails.append("the asset was not written")
        if not note.is_file():
            fails.append("the nested note was not written")
        if (svg.parent / f".{svg.name}.embed.json").exists():
            fails.append("the asset was EMBEDDED — only Markdown is ever eligible")
        if not (note.parent / ".algebra-1--chapter-1.embed.json").exists():
            fails.append("the nested note was not embedded — nesting broke the pipeline")
        if not _git(brain, "ls-files", "--error-unmatch", "--",
                    str(svg.relative_to(brain)), env=env).returncode == 0:
            fails.append("the asset was not committed, so a clone would not have it")

        # --- refusals -----------------------------------------------------------------
        def refuses(label: str, fn, expect: str = "") -> None:
            """Refused, AND for the stated reason.

            Matching any ValueError is too weak: `add_note` refuses an existing note too, so a
            probe aimed at a path that already exists passes on the wrong error and the real
            check never runs. `expect` pins which rule did the refusing.
            """
            try:
                fn()
            except ValueError as exc:
                if expect and expect.lower() not in str(exc).lower():
                    fails.append(f"{label}: refused, but for the wrong reason (wanted "
                                 f"{expect!r}): {str(exc)[:160]}")
                return
            except Exception as exc:
                fails.append(f"{label}: raised the wrong error type ({exc!r})")
                return
            fails.append(f"{label}: was ALLOWED")

        refuses("an orphan asset (no note in the folder)",
                lambda: m.add_asset("projects", "algebra-1/algebra-1--chapter-9", "x.svg", SVG))
        refuses("an asset named *.md",
                lambda: m.add_asset("projects", "algebra-1/algebra-1--chapter-1", "x.md", "hi"))
        refuses("a path traversal in the asset filename",
                lambda: m.add_asset("projects", "algebra-1/algebra-1--chapter-1", "../../x.svg", SVG))
        refuses("overwriting an existing asset",
                lambda: m.add_asset("projects", "algebra-1/algebra-1--chapter-1",
                                    "tile-pattern-cpm-source.svg", SVG))
        refuses("a title whose slug does not fit its folder (the guardrail)",
                lambda: m.add_note("Chapter 2", "projects", "b",
                                   subpath="algebra-1/algebra-1--chapter-1"),
                expect="does not belong")
        # A folder with no note in it yet, so "already exists" cannot mask the real refusal.
        refuses("entry and descriptor together",
                lambda: m.add_note("X", "projects", "b",
                                   subpath="algebra-1/algebra-1--chapter-7",
                                   entry=True, descriptor="y"),
                expect="not both")
        refuses("entry without a subpath",
                lambda: m.add_note("X", "projects", "b", entry=True),
                expect="require subpath")
        for root in ("resources", "areas"):
            refuses(f"a subpath under {root}/",
                    lambda r=root: m.add_note("X", r, "body", subpath="nested"))
        refuses("a traversal in subpath",
                lambda: m.add_note("X", "projects", "body", subpath="../../etc"))
    finally:
        os.chdir(cwd)


def check_tool_descriptions(brain: Path, fails: list[str]) -> None:
    """The rules must reach the MCP client, not just the human reading the docs.

    An assistant in Claude Desktop never sees `CLAUDE.md`, the README, or `docs/`. Its ONLY
    channel is the tool description, so a convention documented everywhere except there is a
    convention it will break — and break plausibly, producing a folder that cannot hold its own
    entry note, or an `![[wikilink]]` image that does not render outside Obsidian.

    `add_note` is where all of this has to land, because it is the tool that chooses the
    filename AND writes the body containing the image reference. Asserting it here is the point:
    the first version of this feature documented every rule in the emitted `CLAUDE.md` and left
    the tool description carrying a worked example (`chapter1/chapter1.md`) that was itself the
    mistake the rule exists to prevent.
    """
    sys.path.insert(0, str(brain / "scripts"))
    for stale in ("mcp_server", "note_view", "features", "db", "search_vault", "add_pdf"):
        sys.modules.pop(stale, None)
    cwd = os.getcwd()
    os.chdir(brain)
    try:
        import mcp_server as m
    except ImportError:
        print("        optional 'mcp' SDK absent — tool descriptions were NOT checked")
        os.chdir(cwd)
        return
    globals()["m"] = m
    try:
        import asyncio
        # Collapse whitespace: a description is a wrapped docstring, so a phrase that reads as
        # one string in the source can be split by a newline plus indentation. The probes are
        # about what the text SAYS, not how it happens to be wrapped.
        tools = {t.name: " ".join((t.description or "").split())
                 for t in asyncio.run(m.mcp.list_tools())}
    finally:
        os.chdir(cwd)

    required = {
        "add_note": [
            ("slugifies", "the folder-naming rule — without it a model picks `chapter1/` and "
                          "the folder can never hold its own entry note"),
            ("chapter-1", "a worked example in the CORRECT kebab-case form"),
            ("entry note", "the entry-note convention"),
            ("unique", "that note filenames must be unique vault-wide, which the hook enforces "
                       "by REFUSING the write"),
            ("![", "the relative-markdown image syntax — add_note writes the body that carries "
                   "the image reference, so this is the only tool that can get it right"),
            ("add_asset", "a pointer to the tool for non-note files"),
        ],
        "add_asset": [
            ("![", "the relative-markdown image syntax"),
            ("add_note", "a pointer back, since the note must exist first"),
            ("never embedded", "that an asset is never embedded"),
        ],
    }
    for tool, probes in required.items():
        if tool not in tools:
            fails.append(f"{tool} is not exposed to MCP clients at all")
            continue
        for probe, why in probes:
            if probe not in tools[tool]:
                fails.append(f"{tool}'s description does not mention {why} — an MCP client sees "
                             f"ONLY this text, so the rule cannot reach it")
    if "chapter1/" in tools.get("add_note", ""):
        fails.append("add_note's description contains the example `chapter1/` — the very "
                     "mistake the slug rule exists to prevent")

    # The FIRST line is all a deferred/collapsed tool index shows. A capability named only in
    # paragraph six is a capability the caller searches for and does not find — so the write
    # tools have to advertise their surface up front or they are, in practice, undiscoverable.
    for tool, needed in (("add_note", ("subpath", "embed")),
                         ("add_asset", ("never embedded",)),
                         ("add_pdf", ("subpath",)),
                         ("get_note_template", ("variant",))):
        first = " ".join(tools.get(tool, "").split(". ")[0].split())
        for word in needed:
            if word not in first:
                fails.append(f"{tool}'s FIRST description line does not name {word!r} — that "
                             f"line is all a collapsed tool index shows, so the capability is "
                             f"invisible until someone already knows to look for it")

    # A documented filename is executable specification: every example must be PRODUCIBLE by
    # the tool meant to create it. The `{folder}--{descriptor}` convention shipped for weeks
    # while being literally unreachable, because the examples were eyeballed and never run.
    # This is the mechanical version of reading them — it asks the composer, not a human.
    import re as _re
    for tool, desc in tools.items():
        for name in _re.findall(r"[a-z0-9][a-z0-9./-]*\.md", desc):
            if "/" not in name:
                continue
            folder, stem = name.rsplit("/", 1)[0].rsplit("/", 1)[-1], name.rsplit("/", 1)[-1][:-3]
            if stem == folder:
                produced = m.compose_note_filename("any title", f"x/{folder}", entry=True)
            elif stem.startswith(f"{folder}--"):
                produced = m.compose_note_filename(
                    "any title", f"x/{folder}", descriptor=stem[len(folder) + 2:])
            else:
                fails.append(f"{tool}'s description shows {name!r}, which does not fit its own "
                             f"folder — add_note's guardrail would REFUSE the very example the "
                             f"description gives")
                continue
            if produced != stem:
                fails.append(f"{tool}'s description shows {name!r}, which add_note cannot "
                             f"produce (it composes {produced!r} instead)")

    # The nested example must be SCOPED to its parent, or the canonical example teaches
    # exactly the name the uniqueness rule rejects — the two sections contradict each other
    # and whoever follows the example hits the hook the day a second subject has a chapter 1.
    for tool in ("add_note",):
        d = tools.get(tool, "")
        if "/chapter-1/chapter-1.md" in d:
            fails.append(f"{tool}'s entry-note example uses a bare `chapter-1/chapter-1.md` — "
                         f"a generic name that collides the moment a second project has a "
                         f"chapter 1, which is precisely what the uniqueness rule forbids")
        for probe in ("entry=True", "descriptor", "algebra-1--chapter-1"):
            if probe not in d:
                fails.append(f"{tool}'s description does not mention {probe!r} — that is how a "
                             f"caller names a file in a folder, and it cannot be guessed")

    # A stale memory outranks a correct description unless the description says otherwise.
    for tool in ("add_note", "add_asset"):
        if "authority" not in tools.get(tool, ""):
            fails.append(f"{tool}'s description does not say it outranks what the caller "
                         f"remembers — a model with a confident, stale picture of this brain "
                         f"will act on the memory and never read far enough to be corrected")


def check_overview(brain: Path, fails: list[str]) -> None:
    """`second_brain_overview` must describe the server it actually runs in.

    Its whole value is being trustworthy in one call, so the failure that matters is drift: a
    tool added later and never mentioned, leaving the one tool that claims to be authoritative
    quietly incomplete. It is generated from the live registry precisely so that cannot happen,
    and this asserts that it really is.
    """
    sys.path.insert(0, str(brain / "scripts"))
    cwd = os.getcwd()
    os.chdir(brain)
    try:
        import asyncio
        import mcp_server as m
        names = {t.name for t in asyncio.run(m.mcp.list_tools())}
        text = asyncio.run(m.second_brain_overview())
    except ImportError:
        os.chdir(cwd)
        return
    finally:
        os.chdir(cwd)

    # Scope this to the TOOL LIST section, not the whole document. Several tool names also
    # appear in the conventions prose, so a whole-text search passes while the inventory itself
    # is missing an entry — which is exactly the drift being guarded against.
    listing = text.split("## Tools available right now", 1)[-1].split("## Conventions", 1)[0]
    for name in sorted(names):
        if f"{name}(" not in listing:
            fails.append(f"second_brain_overview's tool list omits {name!r} — the one place "
                         f"that claims to be the current contract is already incomplete. It is "
                         f"generated from the live registry so that cannot happen; if this "
                         f"fires, something replaced that with a hand-kept list.")
    if not m.INTERFACE_CHANGES:
        fails.append("INTERFACE_CHANGES is empty — the dated list is the only part of the "
                     "overview that can contradict a stale memory; without it the tool only "
                     "restates what a confident caller already believes")
    if "Recent changes" not in text.split("## Tools")[0]:
        fails.append("the recent-changes list is not before the tool list — it is the part "
                     "that corrects a stale caller, so it goes first")
    if "/chapter-1/chapter-1.md" in text:
        fails.append("second_brain_overview's entry-note example uses a bare "
                     "`chapter-1/chapter-1.md`, contradicting the uniqueness rule printed a "
                     "few lines below it")
    for rule in ("subpath", "algebra-1--chapter-1", "entry=True", "descriptor",
                 "unique", "add_asset", "embed: false"):
        if rule not in text:
            fails.append(f"second_brain_overview omits {rule!r} from the conventions it claims "
                         f"to carry")


def check_hint_round_trips(brain: Path, env: dict, fails: list[str]) -> None:
    """The hint's suggested call, executed, must produce the filename the hint claims.

    The previous hint INVERTED the slug — it guessed a title by mapping hyphens back to spaces
    — and so advised a call that could not work: for a `--` folder it suggested a double-SPACE
    title, which slugifies to a single hyphen. Compose forward, never invert; this is the
    assertion that keeps it honest.
    """
    sys.path.insert(0, str(brain / "scripts"))
    cwd = os.getcwd()
    os.chdir(brain)
    try:
        import mcp_server as m
        report = m.add_note("Some Heading", "projects", "body.",
                            subpath="algebra-1/algebra-1--chapter-3", descriptor="scratch")
        hint = [l for l in report.splitlines() if "FOLDER HINT" in l]
        if not hint:
            fails.append("no FOLDER HINT when writing into a folder with no entry note — the "
                         "convention would go unmentioned exactly when it is being broken")
            return
        claimed = re.search(r"creates (\S+?\.md)", hint[0])
        if not claimed:
            fails.append(f"the FOLDER HINT does not name the file it would create: {hint[0]}")
            return
        made = m.add_note("A Readable Heading", "projects", "body.",
                          subpath="algebra-1/algebra-1--chapter-3", entry=True)
        created = re.search(r"created (\S+?\.md)", made)
        if not created:
            fails.append("the hint's own suggested call did not create a note")
        elif Path(created.group(1)).name != claimed.group(1):
            fails.append(f"the FOLDER HINT promised {claimed.group(1)} but its suggested call "
                         f"produced {Path(created.group(1)).name} — the hint is inverting a "
                         f"slug rather than composing forward")
    except ImportError:
        return
    finally:
        os.chdir(cwd)


def check_uniqueness_blocks_a_commit(brain: Path, env: dict, fails: list[str]) -> None:
    """The hook must REFUSE, not warn. A duplicate misroutes links silently and forever."""
    # Collide with a note the payload really created, by hand rather than through add_note —
    # the hook is the backstop for every writer, including a human with an editor, and it is
    # the only thing standing between two same-named notes and silently misrouted wikilinks.
    dup = brain / "vault" / "projects" / "geometry" / "algebra-1--chapter-1"
    dup.mkdir(parents=True, exist_ok=True)
    (dup / "algebra-1--chapter-1.md").write_text(
        "---\ntags: [t]\n---\n\n# Chapter 1\n\nA second one.\n", encoding="utf-8")
    _git(brain, "add", "-A", env=env)
    c = _git(brain, "commit", "-m", "a colliding note", env=env)
    out = c.stdout + c.stderr
    if c.returncode == 0:
        fails.append("a duplicate note filename COMMITTED — every [[algebra-1--chapter-1]] in "
                     "the vault is now ambiguous, and Obsidian resolves it to one of them "
                     "silently")
    elif "algebra-1--chapter-1.md" not in out:
        fails.append(f"the commit was refused without naming the colliding file: {out[-200:]}")
    # Leave the tree CLEAN: the encryption check that follows refuses to migrate a dirty tree,
    # so a leftover staged deletion here fails a later assertion for an unrelated reason.
    _git(brain, "reset", "-q", env=env)
    shutil.rmtree(dup, ignore_errors=True)
    shutil.rmtree(dup.parent, ignore_errors=True)
    _git(brain, "checkout", "-q", "--", ".", env=env)


def check_encrypted_refuses(brain: Path, env: dict, fails: list[str]) -> None:
    """On an encrypted brain the file could not be committed at all, so refuse (#49)."""
    r = _run([PY, "scripts/encrypt_vault.py", "--enable"], brain, env)
    if r.returncode != 0:
        fails.append(f"could not enable encryption for the refusal check: "
                     f"{(r.stderr or r.stdout)[-200:]}")
        return
    sys.path.insert(0, str(brain / "scripts"))
    for stale in ("mcp_server", "features", "encrypt_vault", "passphrase", "note_view"):
        sys.modules.pop(stale, None)
    cwd = os.getcwd()
    os.chdir(brain)
    try:
        import mcp_server as m
        try:
            m.add_asset("projects", "algebra-1/algebra-1--chapter-1", "second.svg", SVG)
        except ValueError as exc:
            if "encrypt" not in str(exc).lower():
                fails.append(f"refused for the wrong reason: {exc}")
        except ImportError:
            pass
        else:
            fails.append("add_asset wrote an asset on an ENCRYPTED brain — the vault is "
                         "git-ignored and only *.md is encrypted, so it reaches no commit in "
                         "any form: the tool would report success and push nothing (#49)")
    finally:
        os.chdir(cwd)


def _step(label: str, ok_line: str, fails: list[str], fn, *args) -> None:
    """Run one check; print its ok line if it added nothing.

    An unexpected exception becomes a NAMED failure rather than a traceback. Several of these
    checks drive `add_note`, which raises on a bad write by design — so a regression in the
    thing under test surfaces as an exception, and an unhandled one both reads worse than an
    assertion and aborts every check that would have run after it, hiding the rest of the
    picture behind the first break.
    """
    before = len(fails)
    try:
        fn(*args)
    except Exception as exc:
        fails.append(f"{label} raised {type(exc).__name__}: {str(exc)[:220]}")
    if len(fails) == before:
        print(f"  ok    {ok_line}")


def main() -> int:
    fails: list[str] = []
    _step("the canonical-view check", "an asset filename never reaches a vector; its alt text "
          "always does", fails, check_projection, fails)

    env = {**os.environ, "SECOND_BRAIN_EMBEDDER": "test",
           "SECOND_BRAIN_PASSPHRASE": "asset gate passphrase",
           "GIT_AUTHOR_NAME": "Asset Check", "GIT_AUTHOR_EMAIL": "asset@example.invalid",
           "GIT_COMMITTER_NAME": "Asset Check", "GIT_COMMITTER_EMAIL": "asset@example.invalid"}
    parent = Path(tempfile.mkdtemp(prefix="asset-coloc-"))
    try:
        brain = parent / "brain"
        _setup(brain, env)
        _step("the payload", "a nested note plus a sibling SVG land, commit, and only the note "
              "embeds; every bad path and orphan is refused",
              fails, check_payload, brain, env, fails)
        _step("the tool-description check", "the naming, uniqueness and image-syntax rules "
              "reach the MCP client in add_note's own description",
              fails, check_tool_descriptions, brain, fails)
        _step("the FOLDER HINT round-trip", "the FOLDER HINT's suggested call really produces "
              "the filename it claims (composed forward, never inverted)",
              fails, check_hint_round_trips, brain, env, fails)
        _step("the overview check", "second_brain_overview lists every live tool, leads with "
              "what changed, and carries the conventions",
              fails, check_overview, brain, fails)
        _step("the uniqueness check", "a duplicate note filename is REFUSED at commit, by name",
              fails, check_uniqueness_blocks_a_commit, brain, env, fails)
        try:
            import cryptography  # noqa: F401
        except ImportError:
            print("        optional 'cryptography' absent — the encrypted refusal was NOT "
                  "exercised")
        else:
            _step("the encrypted-refusal check", "add_asset refuses on an encrypted brain "
                  "rather than reporting a success that commits nothing (#49)",
                  fails, check_encrypted_refuses, brain, env, fails)
    finally:
        shutil.rmtree(parent, ignore_errors=True)

    if fails:
        for f in fails:
            print(f"  FAIL  {f}", file=sys.stderr)
        print(f"\nasset-colocation FAILED: {len(fails)} assertion(s)", file=sys.stderr)
        return 1
    print("asset-colocation OK: a note and its material colocate in a nested project folder — "
          "the asset commits, never embeds, never leaks its filename into a vector, and a "
          "duplicate note name cannot be committed at all")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
