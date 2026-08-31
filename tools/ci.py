#!/usr/bin/env python3
"""The full devkit acceptance gate — one entry point for local **and** CI.

``.github/workflows/ci.yml`` runs exactly this, so a green ``python3 tools/ci.py``
locally predicts a green CI run (local ≡ CI). Everything here is self-contained:
it uses only the in-repo vendored golden (``tests/golden/``, OQ-1 Option A) and the
deterministic ``test`` embedder, so it needs no external golden, no network, and
no third-party packages — just Python 3.11+.

Gate (fail-fast on any red):
  1. **Manifest partition** — emit-manifest.toml partitions the vendored golden.
  2. **Template in sync** — rebuild ``template/`` from the golden and assert the
     committed tree is byte-identical (catches a stale template after a golden
     change). Mutates ``template/`` in place; a clean rebuild leaves it unchanged.
  3. **Emitted scripts compile** — syntax-check every ``.py`` a brain ships (the
     post-clean ``template/`` tree). Byte-diffing proves a file was *copied*, not that
     it *parses*; several emitted scripts (``mcp_server.py``, ``doctor.py``, …) are
     never executed in CI and ``mcp_server.py`` can't even be imported (its optional
     ``mcp`` dep is absent), so a ``SyntaxError`` would otherwise ship green. Pure
     ``compile()`` — no import, no bytecode written, stays stdlib-only.
  4. **Autolink format** — assert ``autolink.py`` emits ``related_auto:`` as *quoted*
     wikilinks in a YAML list (the only form Obsidian graphs; a bare ``[[x]]`` ships
     green but is silently un-graphed — the ``outputSchema`` lesson). Imports the emitted
     ``apply_links`` (db import is lazy → no sqlite-vec); asserts the format independently
     with a negative self-test (``tools/check_autolink_format.py``). Hermetic.
  5. **Mode-A harness** — wipe-regenerate ``sandbox/scratch/`` + guard + in-scaffold
     self-test + structural diff vs the golden (``tools/run_sandbox.py``).
  6. **Mode-B smoke** — ``create_second_brain.py`` into a throwaway temp path, then the same
     structural-diff oracle on it (proves production output ≡ the validated Mode-A
     output).
  7. **Remote-sync** — ``create_second_brain.py --remote`` connect → push → clone-as-peer
     against a local **bare** repo (``file://``). Hermetic (git + stdlib, no network
     or credentials), unlike the Ollama/``mcp`` behavioral checks, so it belongs in
     the gate (``tools/check_remote_sync.py``).
  8. **README managed block** — create a brain, add a user preamble/appendix, let the
     managed body go stale, then ``update_brain --apply`` and assert it **splices**:
     user space preserved, the devkit block regenerated to match ``template/README.md``,
     idempotent, and a marker-less/half-marked README left untouched
     (``tools/check_readme_block.py``). Hermetic (git + stdlib).

    python3 tools/ci.py

This is a devkit tool; it is never emitted into a brain.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS = REPO_ROOT / "tools"
TEMPLATE = REPO_ROOT / "template"  # the post-clean emitted scaffold
PY = sys.executable

# A self-contained git identity so create_second_brain's first commit works even in a bare
# CI runner with no global git config. Only set if the environment lacks one.
GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "devkit-ci",
    "GIT_AUTHOR_EMAIL": "ci@second-brain-devkit.local",
    "GIT_COMMITTER_NAME": "devkit-ci",
    "GIT_COMMITTER_EMAIL": "ci@second-brain-devkit.local",
}


def _run(cmd: list[str], *, cwd: Path | None = None, env: dict | None = None) -> bool:
    result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode == 0


def step_partition() -> bool:
    return _run([PY, str(TOOLS / "check_manifest_partition.py")])


def step_template_in_sync() -> bool:
    # Build a throwaway copy from the golden and compare it to the on-disk
    # template/ — git-state-independent (works whether or not template/ is
    # committed), so this catches a stale template without false-flagging
    # legitimate uncommitted rebuilds.
    tmp = Path(tempfile.mkdtemp(prefix="template-check-"))
    fresh = tmp / "template"
    try:
        if not _run([PY, str(TOOLS / "build_template.py"), str(fresh)]):
            return False
        # -r recursive, --no-dereference compares symlinks by target not content.
        if _run(["diff", "-r", "--no-dereference", str(fresh), str(REPO_ROOT / "template")]):
            print("template/ is in sync with the vendored golden")
            return True
        print("FAIL: template/ differs from a fresh rebuild — run "
              "tools/build_template.py and commit the result", file=sys.stderr)
        return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def step_py_compile() -> bool:
    # Syntax-check every emitted Python file. compile() (not the py_compile module)
    # so nothing is imported and NO .pyc is written into the tracked template/ tree.
    # Catches a SyntaxError in scripts CI never runs (mcp_server.py, doctor.py, …),
    # incl. breakage introduced by the `cleaned` transform (register.py). Hermetic.
    py_files = sorted(TEMPLATE.rglob("*.py"))
    if not py_files:
        print("FAIL: no emitted .py files found under template/", file=sys.stderr)
        return False
    ok = True
    for f in py_files:
        try:
            compile(f.read_text(encoding="utf-8"), str(f.relative_to(REPO_ROOT)), "exec")
        except SyntaxError as exc:
            print(f"FAIL: {f.relative_to(REPO_ROOT)}: {exc}", file=sys.stderr)
            ok = False
    if ok:
        print(f"py-compile OK: {len(py_files)} emitted script(s) parse cleanly")
    return ok


def step_autolink_format() -> bool:
    return _run([PY, str(TOOLS / "check_autolink_format.py")])


def step_mode_a() -> bool:
    return _run([PY, str(TOOLS / "run_sandbox.py")])


def step_mode_b_smoke() -> bool:
    env = {**os.environ, **{k: v for k, v in GIT_IDENTITY.items() if k not in os.environ}}
    parent = Path(tempfile.mkdtemp(prefix="brain-smoke-"))
    target = parent / "brain"
    try:
        if not _run([PY, str(TOOLS / "create_second_brain.py"), str(target)], env=env):
            return False
        return _run([PY, str(TOOLS / "check_structural_diff.py"), str(target)])
    finally:
        shutil.rmtree(parent, ignore_errors=True)


def step_remote_sync() -> bool:
    # Hermetic: git + a file:// bare repo, no network/credentials. Uses the same
    # self-contained identity as the Mode-B smoke so the brain's first commit and
    # the --remote preflight's identity probe both pass on a bare runner.
    env = {**os.environ, **{k: v for k, v in GIT_IDENTITY.items() if k not in os.environ}}
    return _run([PY, str(TOOLS / "check_remote_sync.py")], env=env)


def step_hang_safety() -> bool:
    # Nothing the server does may hang forever (#24): the embedder's HTTP call is timeout-bounded
    # (tested behaviorally against a local wedged socket), and _git spawns non-interactively with
    # DEVNULL stdin, ssh BatchMode, and a caught timeout. Hermetic, stdlib only.
    return _run([PY, str(TOOLS / "check_hang_safety.py")])


def step_doctor_stale() -> bool:
    # doctor.py must detect a stale embedding — a sidecar whose vector predates the note's current
    # canonical view (#30). update_brain ships a new view but never re-embeds, so without this an
    # upgraded brain is silently stale and doctor would still say "healthy". Hermetic: generate,
    # embed (test backend), mutate, assert stale + repair.
    return _run([PY, str(TOOLS / "check_doctor_stale.py")])


def step_config_matrix() -> bool:
    # Exercise NON-DEFAULT config (#29). #28 shipped through a green suite because the toggle that
    # triggers it defaults to false, so the harness never ran the config the user runs. This flips
    # every features.toml toggle off its default at least once, and FAILS if a new toggle ships
    # with no coverage. Hermetic: generates brains, test backend, git + stdlib.
    env = {**os.environ, **{k: v for k, v in GIT_IDENTITY.items() if k not in os.environ}}
    return _run([PY, str(TOOLS / "check_config_matrix.py")], env=env)


def step_note_gate() -> bool:
    # The "what earns a note" gate is deliberately duplicated (CLAUDE.md for an in-repo agent,
    # the note template for Claude Desktop via get_note_template — disjoint audiences that
    # cannot see each other's copy). Duplication is only safe if it can't drift, so this makes
    # drift a build failure instead of a promise. Pure stdlib, no git.
    return _run([PY, str(TOOLS / "check_note_gate.py")])


def step_readme_block() -> bool:
    # Hermetic: create a brain + drive update_brain's README splice (git + stdlib,
    # no Ollama/mcp). Same self-contained identity so the brain's commits pass on a
    # bare runner.
    env = {**os.environ, **{k: v for k, v in GIT_IDENTITY.items() if k not in os.environ}}
    return _run([PY, str(TOOLS / "check_readme_block.py")], env=env)


def step_tag_lint() -> bool:
    # Byte-diffing proves the tag-hygiene scripts were copied; this proves the emitted
    # detector still WORKS — it runs the suite against the vendored bytes and smoke-runs
    # the lint CLI. The lint's informational posture (exit 0 on findings) is in the tool;
    # this gate is the regression check. Hermetic: stdlib + the vendored tree.
    return _run([PY, str(TOOLS / "check_tag_lint.py")])


def step_pdf() -> bool:
    # Byte-diffing proves the PDF modules were copied; this proves they still WORK — it runs
    # the vendored PDF suites (chunk, extract, sidecar, bolt-on cache, passage search, ingest,
    # MCP tools) against the vendored bytes. The optional pypdf/mcp paths skip cleanly, so it
    # stays hermetic (stdlib + sqlite-vec + the vendored tree). Task #7.
    return _run([PY, str(TOOLS / "check_pdf.py")])


def step_encryption() -> bool:
    # Byte-diffing proves the encryption modules were copied; this proves they still WORK.
    # The load-bearing half is note selection: three callers used to ask git what was staged,
    # which returns an EMPTY LIST once the vault is git-ignored — no error, so every caller
    # silently does nothing. Hermetic (stdlib + the vendored tree); the optional cryptography
    # paths skip cleanly, and the gate refuses to count a skip as coverage. Task #42.
    return _run([PY, str(TOOLS / "check_encryption.py")])


def step_classification() -> bool:
    # Which files encryption covers follows update_brain's own preserve rule rather than a
    # hand-kept list; this gate is what makes that a rule instead of a hope. Both directions
    # fail: a preserved file encryption misses would go to a remote in the clear, and an
    # encrypted file the devkit would overwrite breaks upgrades. Hermetic. Task #42.
    return _run([PY, str(TOOLS / "check_content_classification.py")])


def step_encrypted_roundtrip() -> bool:
    # Every other encryption gate proves BYTES round-trip; this proves the brain still works.
    # Sidecars are git-ignored, so a fresh clone has no vectors and an empty cache — the
    # restore path (clone -> decrypt -> embed -> hydrate -> search) is the whole point of
    # having a remote and was never exercised. Bare repo, deterministic embedder, no
    # network; the two-query search assertion fails a search that ignores its query. #42.
    return _run([PY, str(TOOLS / "check_encrypted_roundtrip.py")])


def step_claude_block() -> bool:
    # An UPGRADED brain must receive documentation updates, not just code (#40). CLAUDE.md is
    # now a managed block like the README, plus --adopt for a brain that predates the markers.
    # New brains always looked fine (both files are emitted), which is what hid this — so the
    # gate drives the upgrade path specifically, incl. the note-template drift report that
    # keeps gate 9's invariant honest after an update. Hermetic (git + stdlib).
    env = {**os.environ, **{k: v for k, v in GIT_IDENTITY.items() if k not in os.environ}}
    return _run([PY, str(TOOLS / "check_claude_block.py")], env=env)


def step_embed_excluded() -> bool:
    # The no-embed block must be cut from the embed input AND from the content hash — the
    # same view, or the two disagree and a redrawn diagram both re-embeds and reads stale
    # forever (#39). Also pins the UNMARKED path against a literal digest: drift there
    # would restamp every hash in every existing brain. Hermetic: stdlib + vendored tree.
    return _run([PY, str(TOOLS / "check_embed_excluded.py")])


def step_embed_opt_out() -> bool:
    # `embed: false` lets non-note Markdown live inside a PARA root (#45). Two things rot
    # silently: the parser's polarity (it must fail OPEN — only an explicit false/no/off
    # excludes, or a note you forgot to mark goes silently unsearchable) and RETRACTION
    # (adding the key to an already-indexed file must remove its sidecar, vector and search
    # row, not merely stop refreshing them). Drives real commits through the real hooks.
    return _run([PY, str(TOOLS / "check_embed_opt_out.py")])


STEPS = [
    ("1/20 manifest partition", step_partition),
    ("2/20 template in sync with golden", step_template_in_sync),
    ("3/20 emitted scripts compile", step_py_compile),
    ("4/20 autolink emits Obsidian-graphable frontmatter", step_autolink_format),
    ("5/20 Mode-A harness (generate + guard + self-test + diff)", step_mode_a),
    ("6/20 Mode-B smoke (create_second_brain ≡ Mode-A)", step_mode_b_smoke),
    ("7/20 remote-sync (--remote connect/push/clone, bare repo)", step_remote_sync),
    ("8/20 README managed block (update_brain splices, preserves user space)", step_readme_block),
    ("9/20 note-gate in sync (CLAUDE.md == note template)", step_note_gate),
    ("10/20 config matrix (every toggle exercised off its default)", step_config_matrix),
    ("11/20 doctor detects a stale embedding (and --repair fixes it)", step_doctor_stale),
    ("12/20 hang-safety (embedder timeout + non-interactive git)", step_hang_safety),
    ("13/20 tag hygiene (emitted detector correct + lint CLI wires up)", step_tag_lint),
    ("14/20 pdf ingestion (emitted chunk/extract/cache/search/ingest/mcp suite)", step_pdf),
    ("15/20 embed-excluded block (no-embed cut from both view and hash)", step_embed_excluded),
    ("16/20 upgraded brain receives its docs (CLAUDE.md block + --adopt)", step_claude_block),
    ("17/20 encryption (mechanism + a commit path that does not go blind)", step_encryption),
    ("18/20 content classification (every .md is content or machinery)", step_classification),
    ("19/20 encrypted round-trip (push, destroy, clone, decrypt, search)", step_encrypted_roundtrip),
    ("20/20 embed opt-out (embed: false excludes, retracts, and fails open)", step_embed_opt_out),
]


def main() -> int:
    results: list[tuple[str, bool]] = []
    for name, fn in STEPS:
        print(f"\n=== {name} ===")
        ok = fn()
        results.append((name, ok))
        if not ok:
            print(f"\n✗ CI FAILED at step: {name}")
            # Fail fast: later steps assume earlier ones held.
            for n, r in results:
                print(f"  {'✓' if r else '✗'} {n}")
            return 1

    print("\n✓ CI PASSED — all gates green")
    for n, _ in results:
        print(f"  ✓ {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
