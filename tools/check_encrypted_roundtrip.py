#!/usr/bin/env python3
"""Gate 19 — an encrypted brain survives a remote and still answers questions (#42).

Every other encryption test proves **bytes** round-trip. None proves the brain still
*works* afterwards, and those are different claims. Sidecars are git-ignored, so a fresh
clone arrives with **zero vectors and an empty cache**: decrypting gives you notes and
nothing else. The path that matters — *"my laptop died, restore my brain"* — is

    clone → decrypt → embed → hydrate → search

and until this gate nobody had ever run it end to end.

What it does, in one hermetic pass::

    bare repo  →  generate a brain  →  enable encryption  →  write notes  →  commit
               →  push  →  DELETE THE LOCAL BRAIN ENTIRELY  →  clone
               →  assert the clone holds no notes, only blobs
               →  decrypt  →  embed  →  hydrate  →  search

**A bare repo, not a real remote.** `git push`/`git clone` against one has identical
semantics — only what was committed survives, which is the property under test — while a
network remote would add credentials and flakiness for no extra coverage. Gate 7 already
takes this approach.

**The search assertion is discriminating on purpose.** Two notes, two queries, and each
query must rank *its own* note first. A search that ignored the query and returned a fixed
order would pass a single-query test and fails this one. That matters because the
deterministic `test` embedder makes the vector half meaningless — the lexical FTS5 half is
real regardless of backend, and it is what the assertion actually rests on.

Hermetic: git + stdlib + sqlite-vec, deterministic embedder, no network. Never emitted.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO_ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))
from generate import generate  # noqa: E402

PASSPHRASE = "round-trip gate passphrase"
NOTE_TEMPLATE = "vault/templates/new-note.md"

# Two notes with disjoint, distinctive vocabulary. Each query below must find its own.
NOTES = {
    "vault/resources/kiln-firing-schedule.md": (
        "---\ntags: [ceramics]\n---\n\n# Kiln firing schedule\n\n"
        "A bisque firing climbs to cone 06 slowly so trapped water escapes before the clay "
        "vitrifies. Ramp 80 degrees per hour, hold twenty minutes at the top.\n"),
    "vault/projects/harbour-dredging-permit.md": (
        "---\ntags: [logistics]\n---\n\n# Harbour dredging permit\n\n"
        "The dredging permit requires a sediment survey filed with the port authority before "
        "any spoil is moved to the offshore disposal ground.\n"),
}
QUERIES = {
    "bisque firing cone temperature ramp": "vault/resources/kiln-firing-schedule.md",
    "sediment survey port authority spoil disposal": "vault/projects/harbour-dredging-permit.md",
}


def run(cmd: list[str], cwd: Path, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=600)


def git(root: Path, *args: str, env: dict) -> subprocess.CompletedProcess:
    return run(["git", *args], root, env)


def main() -> int:
    fails: list[str] = []

    def ok(msg): print(f"  ok    {msg}")

    def fail(msg): fails.append(msg); print(f"  FAIL  {msg}")

    try:
        import cryptography  # noqa: F401
    except ImportError:
        print("  note: optional 'cryptography' absent — skipping the encrypted round-trip")
        print("\nround-trip SKIPPED (no cryptography)")
        return 0

    env = {**os.environ,
           "SECOND_BRAIN_EMBEDDER": "test",
           "SECOND_BRAIN_PASSPHRASE": PASSPHRASE,
           "GIT_AUTHOR_NAME": "Round Trip", "GIT_AUTHOR_EMAIL": "rt@example.invalid",
           "GIT_COMMITTER_NAME": "Round Trip", "GIT_COMMITTER_EMAIL": "rt@example.invalid"}

    parent = Path(tempfile.mkdtemp(prefix="roundtrip-"))
    bare, work, fresh = parent / "remote.git", parent / "brain", parent / "restored"
    try:
        subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True, timeout=60)

        # --- build and encrypt -------------------------------------------------
        generate(work)
        git(work, "init", "-q", env=env)
        git(work, "config", "user.email", "rt@example.invalid", env=env)
        git(work, "config", "user.name", "Round Trip", env=env)
        git(work, "config", "commit.gpgsign", "false", env=env)
        git(work, "config", "core.hooksPath", ".githooks", env=env)
        git(work, "add", "-A", env=env)
        git(work, "commit", "-q", "-m", "seed", env=env)

        r = run([sys.executable, "scripts/encrypt_vault.py", "--enable"], work, env)
        if r.returncode != 0:
            fail(f"--enable failed: {(r.stderr or r.stdout).strip()[:200]}")
            return 1

        for rel, body in NOTES.items():
            (work / rel).parent.mkdir(parents=True, exist_ok=True)
            (work / rel).write_text(body, encoding="utf-8")
        c = git(work, "commit", "-q", "--allow-empty", "-m", "notes", env=env)
        if c.returncode != 0:
            fail(f"committing notes failed: {(c.stderr or c.stdout).strip()[:200]}")
            return 1

        expected = {rel: (work / rel).read_bytes()
                    for rel in sorted(p.relative_to(work).as_posix()
                                      for p in (work / "vault").rglob("*.md")
                                      if p.relative_to(work).as_posix() != NOTE_TEMPLATE)}
        ok(f"built an encrypted brain with {len(expected)} note(s)")

        # --- push, then destroy the original -----------------------------------
        git(work, "remote", "add", "origin", str(bare), env=env)
        p = git(work, "push", "-q", "-u", "origin", "HEAD:main", env=env)
        if p.returncode != 0:
            fail(f"push failed: {(p.stderr or p.stdout).strip()[:200]}")
            return 1
        shutil.rmtree(work)
        ok("pushed, then deleted the local brain — the remote is now the only copy")

        # --- clone: what actually survived? ------------------------------------
        c = subprocess.run(["git", "clone", "-q", str(bare), str(fresh)],
                           capture_output=True, text=True, timeout=120)
        if c.returncode != 0:
            fail(f"clone failed: {(c.stderr or c.stdout).strip()[:200]}")
            return 1

        notes_in_clone = [p.relative_to(fresh).as_posix() for p in (fresh / "vault").rglob("*.md")
                          if p.relative_to(fresh).as_posix() != NOTE_TEMPLATE]
        if notes_in_clone:
            fail(f"the clone arrived with PLAINTEXT notes: {notes_in_clone[:5]} — nothing was "
                 f"encrypted, and the remote is holding them in the clear")
        else:
            ok("the clone contains no notes at all — only the encrypted blobs")

        blobs = sorted((fresh / "enc").glob("*.md.enc"))
        if len(blobs) != len(expected):
            fail(f"the clone has {len(blobs)} blob(s) for {len(expected)} note(s)")
        else:
            ok(f"{len(blobs)} encrypted blob(s) survived the round trip")

        for canary in ("kiln-firing-schedule", "harbour-dredging-permit", "bisque", "dredging"):
            hits = subprocess.run(["git", "-C", str(fresh), "grep", "-r", "-i", canary,
                                   "HEAD"], capture_output=True, timeout=120)
            if hits.returncode == 0:
                fail(f"'{canary}' is readable in the clone's history")
        ok("no note name or wording is readable anywhere in the clone")

        # --- restore: the path a user with a dead laptop actually walks ---------
        r = run([sys.executable, "scripts/encrypt_vault.py", "--decrypt"], fresh, env)
        if r.returncode != 0:
            fail(f"--decrypt failed: {(r.stderr or r.stdout).strip()[:200]}")
            return 1
        restored = {rel: (fresh / rel).read_bytes() for rel in expected}
        if restored != expected:
            differing = [rel for rel in expected if restored.get(rel) != expected[rel]]
            fail(f"{len(differing)} note(s) did not restore byte-identically: {differing[:5]}")
        else:
            ok(f"all {len(expected)} note(s) restored byte-identically")

        r = run([sys.executable, "scripts/embed_vault.py"], fresh, env)
        if r.returncode != 0:
            fail(f"embed_vault failed after restore: {(r.stderr or r.stdout).strip()[:200]}")
            return 1
        r = run([sys.executable, "scripts/hydrate_cache.py"], fresh, env)
        if r.returncode != 0:
            fail(f"hydrate_cache failed after restore: {(r.stderr or r.stdout).strip()[:200]}")
            return 1
        ok("re-embedded and hydrated the cache from the restored notes")

        # --- the point: is the knowledge findable again? ------------------------
        for query, want in QUERIES.items():
            r = run([sys.executable, "scripts/search_vault.py", query], fresh, env)
            if r.returncode != 0:
                fail(f"search failed for {query!r}: {(r.stderr or r.stdout).strip()[:160]}")
                continue
            hits = [ln for ln in r.stdout.splitlines() if ".md" in ln]
            if not hits:
                fail(f"search returned nothing for {query!r} — the restored brain answers "
                     f"no questions at all")
            elif want not in hits[0]:
                fail(f"search for {query!r} ranked {hits[0].strip()!r} first, expected {want} "
                     f"— each query must find its OWN note, or the search is not reading the "
                     f"query at all")
            else:
                ok(f"{query!r} → {want}")

    finally:
        shutil.rmtree(parent, ignore_errors=True)

    print()
    if fails:
        print(f"round-trip FAILED: {len(fails)} problem(s)")
        return 1
    print("round-trip OK: pushed, destroyed, cloned, decrypted, re-embedded, and searchable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
