#!/usr/bin/env python3
"""Gate 20 — the ``embed: false`` frontmatter opt-out holds end to end (task #45).

Location alone used to decide what a note is: any Markdown under a PARA root was one. The
opt-out is what lets a project's material live *beside* its note — scratch, a colocated
README, a draft — so the folder archives as one unit. Two things can rot silently here, and
each half of this gate exists for one of them.

**1. The polarity.** Embedding is the default and the parser fails OPEN: only an explicit
``false``/``no``/``off`` excludes; a missing key, a typo, an unterminated frontmatter, or
the key merely mentioned in prose all mean *embed*. Invert that and a note you forgot to
mark becomes **silently unsearchable** — indistinguishable from a note never written, found
out on the day it does not come back. Wrongly embedding costs a stray search hit; wrongly
excluding costs a note. The vendored suite pins this, and this gate re-asserts the load
bearing cases directly so a deleted test cannot take the property with it.

**2. Retraction.** Adding the key to a file that was **already embedded** must remove its
sidecar, its vector and its search row — not merely stop refreshing them. A stale sidecar
left behind keeps being hydrated into the cache, so the file goes on answering searches
while its frontmatter says it is not a note: an exclusion that *appears* to work. That is
why ``update_cache`` routes an excluded note to the DELETE side rather than dropping it from
the upsert list, and why this gate drives real commits through the real hooks instead of
calling the functions — the routing is only observable at the end of the chain.

Also asserts the two visible-consequence properties: ``hydrate_cache`` (a full rebuild from
scratch) must not resurrect an excluded file, and ``doctor`` must neither report it as a
note missing its sidecar nor stay quiet about it — an exclusion nobody can see is the same
failure as a silent one, just moved into the report.

Hermetic: stdlib + git + sqlite-vec, the deterministic ``test`` backend, no Ollama, no
network. Devkit tool, never emitted.

    python3 tools/check_embed_opt_out.py
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
TEMPLATE = REPO_ROOT / "template"
PY = sys.executable

sys.path.insert(0, str(REPO_ROOT / "tools"))
from generate import generate  # noqa: E402

NOTE = "---\ntags: [math]\n---\n\n# Algebra\n\nEntry note for the algebra project.\n"
MATERIAL = "---\nembed: false\n---\n\n# Algebra progress\n\n| Subtest | Score |\n| --- | --- |\n"
MATERIAL_EMBEDDED = MATERIAL.replace("embed: false\n", "tags: [math]\n")


def _run(argv: list[str], cwd: Path, env: dict) -> subprocess.CompletedProcess:
    # -B: never write .pyc into the tree under test.
    return subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True)


def _py(script: str, brain: Path, env: dict, *args: str) -> subprocess.CompletedProcess:
    return _run([PY, "-B", f"scripts/{script}", *args], brain, env)


def _git(brain: Path, *args: str, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=brain, env=env, capture_output=True, text=True)


def _git_init(brain: Path, env: dict) -> None:
    """A real repo with the hooks live — the pre/post-commit pair IS the pipeline under test."""
    _git(brain, "init", "-q", env=env)
    _git(brain, "config", "user.email", "opt-out-check@example.invalid", env=env)
    _git(brain, "config", "user.name", "Opt-out Check", env=env)
    _git(brain, "config", "commit.gpgsign", "false", env=env)
    _git(brain, "config", "core.hooksPath", ".githooks", env=env)
    _git(brain, "add", "-A", env=env)
    _git(brain, "commit", "-q", "-m", "seed brain", env=env)


_CACHE_QUERY = (
    "import sys; sys.path.insert(0, 'scripts');"
    "from db import connect;"
    "print('\\n'.join(r[0] for r in "
    "connect('data/brain.db').execute('SELECT source_file FROM notes')))"
)


def _cached(brain: Path, env: dict) -> set[str]:
    """Every note path the search cache would answer with.

    Read through the brain's OWN ``db.connect`` in a subprocess: ``notes`` is a ``vec0``
    virtual table, so a plain ``sqlite3.connect`` here cannot even open it, and the brain
    already owns the one connection path that loads the extension.
    """
    r = subprocess.run([PY, "-B", "-c", _CACHE_QUERY], cwd=brain, env=env,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"embed-opt-out: cannot read the cache: {r.stderr.strip()[-300:]}")
    return {line for line in r.stdout.splitlines() if line}


def check_parser(fails: list[str]) -> None:
    """The polarity, re-asserted against the vendored module itself."""
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(GOLDEN / "scripts"))
    try:
        import note_view as nv
    except ImportError as exc:
        fails.append(f"cannot import the vendored note_view: {exc}")
        return

    for text, why in [
        ("---\nembed: false\n---\n\n# F\n", "the plain key"),
        ("---\ntags: [t]\nembed: no\n---\n\n# F\n", "'no', below another key"),
        ("---\nembed: OFF\n---\n\n# F\n", "'OFF', uppercase"),
    ]:
        if not nv.embed_excluded(text):
            fails.append(f"embed_excluded missed {why} — the opt-out does not opt out")

    for text, why in [
        ("---\ntags: [t]\n---\n\n# N\n", "a note with no embed key"),
        ("---\nembed: true\n---\n\n# N\n", "embed: true"),
        ("---\nembed: fasle\n---\n\n# N\n", "a TYPO in the value"),
        ("---\ntags: [t]\n---\n\n# N\n\nSet `embed: false` to opt out.\n", "the key in PROSE"),
        ("---\ntags: [t]\n\n# N\n", "unterminated frontmatter"),
        ("# N\n\nNo frontmatter at all.\n", "no frontmatter"),
    ]:
        if nv.embed_excluded(text):
            fails.append(f"embed_excluded EXCLUDED {why} — the parser stopped failing open, so "
                         f"a note nobody meant to exclude is now silently unsearchable")


def check_templates(fails: list[str]) -> None:
    """The shipped starting point must be what it claims — in the EMITTED tree, not just the golden."""
    tpl = TEMPLATE / "seeds" / "templates" / "not-a-note.md"
    if not tpl.is_file():
        fails.append("template/seeds/templates/not-a-note.md is missing — an MCP client asking "
                     "for the not-a-note variant would get nothing, and a user has no starting "
                     "point for the excluded case")
        return
    import note_view as nv  # already imported + on the path by check_parser
    if not nv.embed_excluded(tpl.read_text(encoding="utf-8")):
        fails.append("the shipped not-a-note template does NOT actually opt out — copying it "
                     "into a PARA root would embed the file it promises to keep out")
    if nv.embed_excluded((TEMPLATE / "seeds" / "templates" / "new-note.md").read_text("utf-8")):
        fails.append("the DEFAULT note template carries the opt-out — every note started from "
                     "it would be silently unsearchable")


def drive(brain: Path, env: dict, fails: list[str]) -> None:
    folder = brain / "vault" / "projects" / "algebra"
    folder.mkdir(parents=True)
    note, material = folder / "algebra.md", folder / "algebra--progress.md"
    note.write_text(NOTE, encoding="utf-8")
    material.write_text(MATERIAL_EMBEDDED, encoding="utf-8")
    sidecar = folder / ".algebra.embed.json"
    mat_sidecar = folder / ".algebra--progress.embed.json"
    rel_note, rel_mat = "vault/projects/algebra/algebra.md", "vault/projects/algebra/algebra--progress.md"

    # 1. Both files start as notes, so the bulk retraction below starts from a real vector.
    r = _py("embed_vault.py", brain, env)
    if r.returncode != 0:
        fails.append(f"embed_vault failed: {r.stderr.strip()[-300:]}")
        return
    if not sidecar.exists():
        fails.append("the colocated NOTE was not embedded — PARA roots must walk recursively, "
                     "or the whole colocation pattern is dead")
    if not mat_sidecar.exists():
        fails.append("the material did not embed before it was marked — the bulk retraction "
                     "below would then prove nothing")

    # 2. Bulk retraction. `embed_vault` is the ONLY path where dropping the stale sidecar is
    #    load-bearing: on the commit path `update_cache.delete()` unlinks it as part of
    #    removing the row, but nothing follows a bulk re-embed. Leave the sidecar here and the
    #    next `hydrate_cache` puts the vector straight back — an exclusion that looks like it
    #    worked until the day the file answers a search.
    material.write_text(MATERIAL, encoding="utf-8")
    r = _py("embed_vault.py", brain, env)
    if r.returncode != 0:
        fails.append(f"embed_vault failed after the opt-out: {r.stderr.strip()[-300:]}")
        return
    if mat_sidecar.exists():
        fails.append("embed_vault left the STALE SIDECAR of a newly-excluded file in place — "
                     "the next hydrate_cache resurrects its vector, so the exclusion appears "
                     "to work and does not")
    if "excluded by embed: false" not in r.stdout:
        fails.append("embed_vault did not report the exclusion — the note count just comes out "
                     "smaller than the file count with nothing explaining the gap")

    # 3. A full rebuild from scratch must not resurrect it either.
    if _py("hydrate_cache.py", brain, env).returncode != 0:
        fails.append("hydrate_cache failed")
        return
    cached = _cached(brain, env)
    if rel_note not in cached:
        fails.append(f"the colocated note is missing from the cache: {sorted(cached)}")
    if rel_mat in cached:
        fails.append("hydrate_cache RESURRECTED an excluded file into the search cache")

    # 4. doctor: clean, and the exclusion is visible rather than counted as a missing sidecar.
    rc, out = (lambda p: (p.returncode, p.stdout + p.stderr))(_py("doctor.py", brain, env))
    if "excluded by embed: false" not in out:
        fails.append("doctor does not report the excluded count — an exclusion nobody can see "
                     "is the same failure as a silent one, just moved into the report")
    if "note(s) without a sidecar" in out or "missing sidecar" in out:
        fails.append(f"doctor reported the excluded file as a note missing its sidecar — "
                     f"--repair would then embed the very file the key exists to keep out")
    if rc != 0:
        fails.append(f"doctor is not clean on a brain with an excluded file: {out[-400:]}")

    # 5. The retraction path through the real HOOKS (a different mechanism from
    #    step 2: update_cache's routing, not embed_staged's sidecar drop). Commit the material WITHOUT the key
    #    first, so it is genuinely in the brain, then add the key and commit again.
    material.write_text(MATERIAL_EMBEDDED, encoding="utf-8")
    _git(brain, "add", "-A", env=env)
    c = _git(brain, "commit", "-q", "-m", "material as a note", env=env)
    if c.returncode != 0:
        fails.append(f"commit failed: {c.stderr.strip()[-300:]}")
        return
    if not mat_sidecar.exists():
        fails.append("the material did not embed without the key — the retraction test below "
                     "would then prove nothing (it must start from a genuinely indexed file)")
    if rel_mat not in _cached(brain, env):
        fails.append("the material did not reach the cache without the key — same problem")

    material.write_text(MATERIAL, encoding="utf-8")
    _git(brain, "add", "-A", env=env)
    c = _git(brain, "commit", "-q", "-m", "opt the material out", env=env)
    if c.returncode != 0:
        fails.append(f"commit failed: {c.stderr.strip()[-300:]}")
        return
    if mat_sidecar.exists():
        fails.append("adding embed: false left the STALE SIDECAR in place — the next hydrate "
                     "puts the vector straight back, so the exclusion appears to work and does not")
    after = _cached(brain, env)
    if rel_mat in after:
        fails.append("adding embed: false did NOT retract the search row — the file goes on "
                     "answering searches while its frontmatter says it is not a note "
                     "(update_cache must route an excluded note to the DELETE side, not just "
                     "drop it from the upsert list)")
    if rel_note not in after:
        fails.append("retracting the material also dropped the sibling NOTE from the cache")

    # 6. And back: deleting the key returns the file to the brain.
    material.write_text(MATERIAL_EMBEDDED, encoding="utf-8")
    _git(brain, "add", "-A", env=env)
    _git(brain, "commit", "-q", "-m", "opt it back in", env=env)
    if rel_mat not in _cached(brain, env):
        fails.append("deleting the key did not put the file back in the brain — the opt-out is "
                     "one-way, so a mistake is unrecoverable without a manual rebuild")


def main() -> int:
    fails: list[str] = []

    suite = GOLDEN / "tests" / "test_embed_opt_out.py"
    if not suite.is_file():
        print("FAIL: vendored tests/test_embed_opt_out.py missing (run tools/vendor_golden.py)",
              file=sys.stderr)
        return 1
    r = subprocess.run([PY, "-B", str(suite)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.stdout.write(r.stdout)
        sys.stderr.write(r.stderr)
        fails.append("the emitted embed-opt-out parser regressed (vendored suite red)")

    check_parser(fails)
    check_templates(fails)

    env = {**os.environ, "SECOND_BRAIN_EMBEDDER": "test"}
    parent = Path(tempfile.mkdtemp(prefix="embed-opt-out-"))
    try:
        brain = parent / "brain"
        generate(brain)
        _git_init(brain, env)
        drive(brain, env, fails)
    finally:
        shutil.rmtree(parent, ignore_errors=True)

    if fails:
        for f in fails:
            print(f"  FAIL  {f}", file=sys.stderr)
        print(f"\nembed-opt-out FAILED: {len(fails)} assertion(s)", file=sys.stderr)
        return 1

    print("embed-opt-out OK: parser fails open (only explicit false/no/off excludes); the "
          "shipped not-a-note template really opts out; a colocated note embeds while its "
          "material does not; hydrate does not resurrect it; doctor reports the exclusion "
          "instead of calling it a missing sidecar; and adding the key to an indexed file "
          "retracts its sidecar AND its search row — reversibly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
