#!/usr/bin/env python3
"""Gate 24 — the `lexical-only` fence keeps a region out of the vector and IN keyword search.

Search here is **hybrid**: BM25 over an FTS5 index fused with a vector KNN. The two halves are
good at different things, and until this fence existed one marker excluded a region from both.
That is right for what it was built for (ASCII art has no meaning to retrieve by either way)
and wrong for reference data — an ID or a phone number is a *token*, not a meaning. It dilutes
an embedding and it is precisely what BM25 nails.

Three properties, each failing differently:

1. **The split itself.** A `lexical-only` region must be absent from the vector's input and
   present in the lexical row. Regress it one way and IDs pollute every vector; the other way
   and they become unfindable by any means, which is the loss that motivated the fence.
2. **Narrowness.** `lexical_body` must differ from `canonical_body` in **exactly one** way. #39
   showed that the embedding, the content hash and the lexical index drift apart the moment
   they are computed from projections differing in more than one place — so a note with no
   `lexical-only` region must project identically through both.
3. **Free edits.** The region is outside the content hash, so changing a phone number or
   ticking a checkbox must NOT re-embed — while the lexical row still refreshes, because
   `index_fts` runs on every upsert regardless of the hash. That combination is the feature.

Also asserts what a malformed fence costs. An unpaired or nested marker excludes **nothing**,
silently: the note commits, renders correctly, and carries into the index exactly what the
marker was added to keep out. `check_fences.py` must catch it and the pre-commit hook must
refuse the commit.

Hermetic: stdlib + git + sqlite-vec, deterministic `test` backend, no Ollama. Never emitted.

    python3 tools/check_lexical_fence.py
"""
from __future__ import annotations

import os
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

ID, PHONE, ART = "REG-066388", "408-453-6767", "BOXDRAWNROADMAP"


def _run(argv: list[str], cwd: Path, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run([argv[0], "-B", *argv[1:]], cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=600)


def _git(brain: Path, *args: str, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=brain, env=env,
                          capture_output=True, text=True, timeout=120)


def _fts(brain: Path, env: dict, rel: str) -> str:
    q = ("import sys; sys.path.insert(0, 'scripts');"
         "from db import connect;"
         "print(next((r[0] for r in connect('data/brain.db').execute("
         "'SELECT body FROM notes_fts WHERE source_file = ?', (sys.argv[1],))), ''))")
    return _run([PY, "-c", q, rel], brain, env).stdout


def check_projections(fails: list[str]) -> None:
    """Assert the split and its narrowness against the vendored module."""
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(GOLDEN / "scripts"))
    import note_view as nv

    LB, LE = nv.LEXICAL_ONLY_BEGIN, nv.LEXICAL_ONLY_END
    NB, NE = nv.NO_EMBED_BEGIN, nv.NO_EMBED_END

    def note(body):
        return f"---\ntags: [t]\n---\n\n# N\n\n{body}\n"

    t = note(f"prose\n\n{NB}\n{ART}\n{NE}\n\n{LB}\n{ID} {PHONE}\n{LE}")
    if ID in nv.canonical_body(t):
        fails.append("a lexical-only region reached the EMBED input — identifiers dilute the "
                     "vector, which is the whole reason the fence exists")
    if ID not in nv.lexical_body(t) or PHONE not in nv.lexical_body(t):
        fails.append("a lexical-only region is missing from the LEXICAL view — it would be "
                     "unfindable by any means, the loss this fence was built to undo")
    if ART in nv.lexical_body(t):
        fails.append("a no-embed region reached the lexical view — art has no meaning to "
                     "retrieve by in either half, and no-embed must still cut both")
    if "second-brain:" in nv.lexical_body(t):
        fails.append("the fence markers themselves are indexed — every fenced note would match "
                     "a search for 'second-brain' or 'lexical-only'")

    # Narrowness: with no lexical-only region, the two views must be byte-identical.
    for body in ("plain prose", f"a\n{NB}\nX\n{NE}\nb", "a [[link]] and ![alt](x.svg)"):
        if nv.canonical_body(note(body)) != nv.lexical_body(note(body)):
            fails.append(f"the two projections differ on a note with NO lexical-only region "
                         f"({body!r}) — they must differ in exactly one way, or the embedding, "
                         f"the hash and the lexical index start drifting apart")

    # Free edits: the region is outside the content hash.
    a = note(f"p\n\n{LB}\n- [ ] TB test / {PHONE}\n{LE}")
    b = note(f"p\n\n{LB}\n- [x] TB test / 408-000-0000\n{LE}")
    if nv.content_hash(a) != nv.content_hash(b):
        fails.append("editing inside a lexical-only fence changed the content hash — it would "
                     "re-embed on every checkbox tick, which is what the fence avoids")
    if nv.lexical_body(a) == nv.lexical_body(b):
        fails.append("editing inside a lexical-only fence did not change the lexical view — "
                     "the edit would never reach keyword search")

    # Validation: unpaired, nested and interleaved are all refused.
    for label, text in (("unpaired", note(f"{LB}\nx")),
                        ("nested", note(f"{NB}\n{LB}\nx\n{LE}\n{NE}")),
                        ("interleaved", note(f"{NB}\n{LB}\nx\n{NE}\n{LE}"))):
        if not nv.fence_errors(text):
            fails.append(f"a {label} fence was accepted — it excludes NOTHING, so the region "
                         f"the author fenced is embedded anyway and nothing says so")
    if nv.fence_errors(note(f"{NB}\na\n{NE}\n\n{LB}\nb\n{LE}")):
        fails.append("two sequential fences were rejected — that is the normal case")

    suite = GOLDEN / "tests" / "test_lexical_fence.py"
    if not suite.is_file():
        fails.append("vendored tests/test_lexical_fence.py missing (run vendor_golden.py)")
    elif subprocess.run([PY, "-B", str(suite)], capture_output=True).returncode != 0:
        fails.append("the emitted lexical-fence suite regressed")


def check_end_to_end(brain: Path, env: dict, fails: list[str]) -> None:
    """Drive a real commit: the ID must be searchable, and must not be in the vector's input."""
    generate(brain)
    for cmd in (["init", "-q"], ["config", "user.email", "f@example.invalid"],
                ["config", "user.name", "Fence"], ["config", "commit.gpgsign", "false"],
                ["config", "core.hooksPath", ".githooks"]):
        _git(brain, *cmd, env=env)
    _git(brain, "add", "-A", env=env)
    _git(brain, "commit", "-q", "-m", "seed", env=env)
    for script in ("embed_vault.py", "hydrate_cache.py"):
        _run([PY, f"scripts/{script}"], brain, env)

    sys.path.insert(0, str(GOLDEN / "scripts"))
    import note_view as nv
    rel = "vault/resources/permit-refs.md"
    (brain / rel).write_text(
        f"---\ntags: [t]\n---\n\n# Permit refs\n\nHow the county recommendation works.\n\n"
        f"{nv.LEXICAL_ONLY_BEGIN}\nSCCOE ref {ID}, Credential Services {PHONE}\n"
        f"{nv.LEXICAL_ONLY_END}\n", encoding="utf-8")
    _git(brain, "add", "-A", env=env)
    c = _git(brain, "commit", "-q", "-m", "note: permit refs", env=env)
    if c.returncode != 0:
        fails.append(f"committing a fenced note failed: {(c.stderr or c.stdout)[-200:]}")
        return

    body = _fts(brain, env, rel)
    if ID not in body:
        fails.append(f"{ID} is not in the lexical row after a real commit — the fenced region "
                     f"never reached keyword search")
    sidecar = brain / "vault" / "resources" / ".permit-refs.embed.json"
    if sidecar.exists() and ID in sidecar.read_text(encoding="utf-8"):
        fails.append("the identifier reached the sidecar — it is in the vector's input")

    # A malformed fence must fail the commit, not slip through.
    (brain / rel).write_text(
        f"---\ntags: [t]\n---\n\n# Permit refs\n\nprose\n\n{nv.LEXICAL_ONLY_BEGIN}\nunclosed\n",
        encoding="utf-8")
    _git(brain, "add", "-A", env=env)
    c = _git(brain, "commit", "-q", "-m", "broken fence", env=env)
    if c.returncode == 0:
        fails.append("a note with an UNPAIRED fence committed — the region it was meant to "
                     "exclude is now in the vector, and nothing reported it")
    elif "lexical-only" not in (c.stdout + c.stderr):
        fails.append(f"the commit was refused without naming the broken fence: "
                     f"{(c.stdout + c.stderr)[-200:]}")


def main() -> int:
    fails: list[str] = []
    try:
        check_projections(fails)
    except Exception as exc:
        fails.append(f"the projection check raised {type(exc).__name__}: {str(exc)[:200]}")
    if not fails:
        print("  ok    lexical-only leaves the vector and the hash, stays in keyword search; "
              "the two projections differ in exactly one way")

    env = {**os.environ, "SECOND_BRAIN_EMBEDDER": "test",
           "GIT_AUTHOR_NAME": "Fence", "GIT_AUTHOR_EMAIL": "f@example.invalid",
           "GIT_COMMITTER_NAME": "Fence", "GIT_COMMITTER_EMAIL": "f@example.invalid"}
    parent = Path(tempfile.mkdtemp(prefix="lexical-fence-"))
    try:
        before = len(fails)
        try:
            check_end_to_end(parent / "brain", env, fails)
        except Exception as exc:
            fails.append(f"the end-to-end check raised {type(exc).__name__}: {str(exc)[:200]}")
        if len(fails) == before:
            print("  ok    through a real commit: the ID is keyword-searchable and absent from "
                  "the sidecar; a malformed fence is refused by name")
    finally:
        shutil.rmtree(parent, ignore_errors=True)

    if fails:
        for f in fails:
            print(f"  FAIL  {f}", file=sys.stderr)
        print(f"\nlexical-fence FAILED: {len(fails)} assertion(s)", file=sys.stderr)
        return 1
    print("lexical-fence OK: reference data stays out of the vector and in keyword search, "
          "editing it never re-embeds, and a fence that excludes nothing cannot be committed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
