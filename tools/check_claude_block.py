#!/usr/bin/env python3
"""Gate 16 — an upgraded brain actually RECEIVES documentation updates (task #40).

Gate 8 proves the README splice works. This proves the harder half that #40 exposed: a
brain created before a feature took the *code* and never the *prose that says the code
exists*, because `CLAUDE.md` was preserved wholesale. New brains were always fine — both
files are emitted — which is precisely what made it invisible: every
generate-from-scratch check passed, and only a real, upgraded brain was missing the docs.

So this exercises the paths a from-scratch check cannot reach:

  1. A fresh brain ships `CLAUDE.md` **with** the managed markers.
  2. A stale managed block is **spliced** current, and the user's own text above and below
     the markers survives byte-for-byte.
  3. The splice is **idempotent** — a second update is a no-op.
  4. A **marker-less** `CLAUDE.md` (the pre-#40 brain) is NOT silently skipped: the update
     names it, says the directives will not reach this brain, and points at `--adopt`.
  5. `--adopt` brings it under management **without losing a byte** — devkit block first
     (an agent reads top-down), the user's previous file kept verbatim below — and the
     brain is genuinely managed afterwards: the next ordinary update splices it.
  6. A half-marked file is left alone rather than guessed at.
  7. **Gate 9 still holds after an upgrade.** The "what earns a note" gate is duplicated
     into the note template on purpose, and CI requires the two to match byte-for-byte —
     but the template lives under the preserved `vault/`, so an upgrade can leave a brain
     violating an invariant the devkit enforces at build time. update_brain must SAY so.

Hermetic: git + stdlib, no Ollama / mcp / network.

    python3 tools/check_claude_block.py

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
PY = sys.executable

# Single source of truth for the markers and the adoption rule: import from the tool under
# test so this gate can never drift from it.
sys.path.insert(0, str(TOOLS))
from update_brain import ADOPTABLE, BEGIN, CLAUDE, END, README, _managed_body  # noqa: E402

GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "devkit-ci",
    "GIT_AUTHOR_EMAIL": "ci@second-brain-devkit.local",
    "GIT_COMMITTER_NAME": "devkit-ci",
    "GIT_COMMITTER_EMAIL": "ci@second-brain-devkit.local",
}
ENV = {**os.environ, **{k: v for k, v in GIT_IDENTITY.items() if k not in os.environ}}

PREAMBLE = "# My own house rules\n\nAlways greet me in Latin.\n"
APPENDIX = "\n## Scratch\n\n- remember to prune the archive\n"


class CheckError(Exception):
    """A failed assertion, reported with context."""


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, env=ENV, capture_output=True, text=True)


def _git(repo: Path, *args: str) -> None:
    r = _run(["git", "-C", str(repo), *args])
    if r.returncode != 0:
        raise CheckError(f"git {' '.join(args)} failed: {r.stderr.strip()}")


def _update(brain: Path, *flags: str) -> str:
    r = _run([PY, str(TOOLS / "update_brain.py"), str(brain), *flags])
    if r.returncode != 0:
        raise CheckError(f"update_brain {' '.join(flags)} failed: {r.stdout}{r.stderr}")
    return r.stdout


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise CheckError(msg)


def _commit_all(brain: Path, msg: str) -> None:
    _git(brain, "add", "-A")
    _git(brain, "commit", "-q", "--no-verify", "-m", msg)


def run_checks() -> None:
    parent = Path(tempfile.mkdtemp(prefix="claude-block-"))
    brain = parent / "brain"
    try:
        # 1. a fresh brain ships the markers -------------------------------------------
        r = _run([PY, str(TOOLS / "create_second_brain.py"), str(brain)])
        if r.returncode != 0:
            raise CheckError(f"create_second_brain failed: {r.stdout}{r.stderr}")
        claude = brain / CLAUDE
        text = claude.read_text()
        _require(BEGIN in text and END in text,
                 "a generated brain's CLAUDE.md lacks the managed-block markers")
        _require(CLAUDE in ADOPTABLE, "CLAUDE.md is not registered as adoptable")
        print("  ok    a generated brain ships CLAUDE.md with the managed markers")

        # GEMINI.md is a symlink to CLAUDE.md — it must follow, not fork.
        gemini = brain / "GEMINI.md"
        _require(gemini.is_symlink() and os.readlink(gemini) == CLAUDE,
                 "GEMINI.md is not a symlink to CLAUDE.md — it would fork from the managed block")
        print("  ok    GEMINI.md still symlinks to CLAUDE.md (one managed block, two names)")

        # 2. user space survives a splice ----------------------------------------------
        stale = text.replace(_managed_body(text), "OLD DEVKIT BODY — should be replaced")
        claude.write_text(PREAMBLE + "\n" + stale + APPENDIX)
        _commit_all(brain, "personalise CLAUDE.md and let the block go stale")
        _update(brain, "--apply")
        got = claude.read_text()
        _require(got.startswith(PREAMBLE), "the user's preamble was not preserved byte-for-byte")
        _require(got.endswith(APPENDIX), "the user's appendix was not preserved byte-for-byte")
        _require("OLD DEVKIT BODY" not in got, "the stale managed body was not regenerated")
        _require(_managed_body(claude.read_text()) == _managed_body(text),
                 "the regenerated body does not match the template's")
        print("  ok    a stale block is spliced current; user space above and below is untouched")

        # 3. idempotent -----------------------------------------------------------------
        before = claude.read_text()
        out = _update(brain, "--apply")
        _require(claude.read_text() == before,
                 "a second update changed CLAUDE.md — the splice is not idempotent")
        _require("already up to date" in out, f"expected a no-op update, got:\n{out}")
        print("  ok    re-running the update is a byte-exact no-op")

        # 4. the pre-#40 brain is NAMED, not silently skipped ---------------------------
        # This is the whole bug: markers absent -> nothing happens -> nobody is told.
        legacy = PREAMBLE + "\n" + _managed_body(text) + APPENDIX
        claude.write_text(legacy)
        _commit_all(brain, "simulate a brain that predates the managed CLAUDE.md")
        out = _update(brain)
        _require("CLAUDE.md" in out and "--adopt" in out,
                 f"a marker-less CLAUDE.md was not reported with the --adopt remedy:\n{out}")
        _require("will NOT reach it" in out,
                 f"the report does not say the directives will not arrive:\n{out}")
        _require(claude.read_text() == legacy,
                 "a marker-less CLAUDE.md was modified WITHOUT --adopt")
        # The subtler half of the same bug: reporting the gap and then signing off with
        # "already up to date" restores exactly the silence this feature exists to end.
        _require("already up to date" not in out,
                 f"a brain missing its directives was called up to date:\n{out}")
        _require("NOT under management" in out,
                 f"the summary line does not name the unmanaged file:\n{out}")
        print("  ok    a marker-less CLAUDE.md is named loudly and left alone without --adopt")
        print("  ok    and the run does NOT sign off as 'already up to date'")

        # 5. --adopt brings it under management, losing nothing --------------------------
        _update(brain, "--apply", "--adopt")
        got = claude.read_text()
        _require(got.startswith(BEGIN),
                 "adoption did not put the devkit block first (an agent reads top-down)")
        _require(legacy.strip() in got,
                 "adoption dropped part of the user's previous file — it must be kept verbatim")
        _require(_managed_body(got) == _managed_body(text),
                 "the adopted block does not match the template's body")
        print("  ok    --adopt writes the block first and keeps the previous file verbatim")

        # --apply commits its own work, so adoption must leave a clean tree; if it did not,
        # the next scenario's _commit_all would silently sweep the leftovers into itself.
        _require(not _run(["git", "-C", str(brain), "status", "--porcelain"]).stdout.strip(),
                 "--adopt --apply left the brain dirty instead of committing its own change")
        out = _update(brain)
        _require("already up to date" in out,
                 f"an adopted CLAUDE.md is not managed on the next run:\n{out}")
        print("  ok    an adopted brain is genuinely managed from then on")

        # 6. half-marked -> leave it alone, don't guess a boundary ------------------------
        claude.write_text(BEGIN + "\n" + _managed_body(text) + "\n")  # begin, no end
        _commit_all(brain, "half-marked CLAUDE.md")
        before = claude.read_text()
        out = _update(brain, "--apply", "--adopt")
        _require(claude.read_text() == before,
                 "a half-marked CLAUDE.md was rewritten — the boundary must not be guessed")
        _require("one marker without its partner" in out,
                 f"a half-marked CLAUDE.md was not reported:\n{out}")
        print("  ok    a half-marked CLAUDE.md is reported and left untouched")

        # 6b. the README is adoptable on the same terms -----------------------------------
        # Adoption was first built for CLAUDE.md only, on the theory that a stale README is at
        # least visible to its reader. That theory was wrong: the real brain's README was
        # missing a whole feature section, and absence is invisible to a reader too. Same
        # mechanism, same consent flag — asserted here so the two files cannot drift apart.
        _require(README in ADOPTABLE, "README.md is not adoptable — it must be, per #40 §6")
        readme = brain / README
        plain = "# My brain\n\nJust my own words, no markers anywhere.\n"
        readme.write_text(plain)
        _commit_all(brain, "a README that predates the managed block")
        out = _update(brain)
        _require(readme.read_text() == plain, "a marker-less README changed WITHOUT --adopt")
        _require("--adopt" in out, f"adoption was not offered for the README:\n{out}")
        _update(brain, "--apply", "--adopt")
        got = readme.read_text()
        _require(got.startswith(BEGIN), "README adoption did not put the devkit block first")
        _require(plain.strip() in got, "README adoption dropped the user's previous file")
        print("  ok    a marker-less README is adoptable on the same terms as CLAUDE.md")

        # 7. the note template is REFRESHED, closing the gate-9 hole ----------------------
        # vault/templates/new-note.md carries the note gate that gate 9 requires to match
        # CLAUDE.md. It lives in the vault only because that is where Obsidian's Templates
        # plugin can reach it — so it is the one named exception to "never write into vault/".
        # Left frozen, an upgraded brain could violate a build-time invariant.
        note_tpl = brain / "vault" / "templates" / "new-note.md"
        _require(note_tpl.is_file(), "the brain has no vault/templates/new-note.md")
        note_tpl.write_text("stale drift\n")
        _commit_all(brain, "let the vault note template drift from the seed")
        out = _update(brain)
        _require("vault/templates/new-note.md" in out,
                 f"the drifted note template was not picked up:\n{out}")
        _update(brain, "--apply")
        got = note_tpl.read_text()
        _require("stale drift" not in got, "the drifted note template was not refreshed")
        _require(got == (brain / "seeds" / "templates" / "new-note.md").read_text(),
                 "the refreshed note template does not match the emitted seed")
        print("  ok    the devkit-owned note template is refreshed from the seed")

        # The same for the not-a-note variant (#45). It matters for a different reason: the
        # MCP tool get_note_template("not-a-note") READS this file out of the vault, so an
        # upgraded brain that never received it would ship the tool and answer with a
        # fallback string — the feature present in the code and absent from the brain.
        alt_tpl = brain / "vault" / "templates" / "not-a-note.md"
        _require(alt_tpl.is_file(), "the brain has no vault/templates/not-a-note.md")
        alt_tpl.unlink()
        _commit_all(brain, "an upgraded brain that predates the not-a-note template")
        out = _update(brain)
        _require("vault/templates/not-a-note.md" in out,
                 f"the missing not-a-note template was not picked up:\n{out}")
        _update(brain, "--apply")
        _require(alt_tpl.is_file() and
                 alt_tpl.read_text() == (brain / "seeds" / "templates" / "not-a-note.md").read_text(),
                 "the not-a-note template was not delivered to an upgraded brain")
        print("  ok    ...and an upgraded brain receives the not-a-note template it lacked")

        # ...and the exception is exactly those two files. A real note must survive untouched.
        canary = brain / "vault" / "resources" / "my-own-note.md"
        canary.write_text("---\ntags: [mine]\n---\n\n# Mine\n\nDo not touch.\n")
        _commit_all(brain, "a user note in the vault")
        _update(brain, "--apply")
        _require(canary.read_text().endswith("Do not touch.\n"),
                 "update_brain wrote into a user's note — the vault carve-out is too wide")
        print("  ok    ...and vault/templates/ is the ONLY place written inside vault/")

    finally:
        shutil.rmtree(parent, ignore_errors=True)


def main() -> int:
    try:
        run_checks()
    except CheckError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("\nclaude-block OK: an upgraded brain receives its directives (splice, adopt, report)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
