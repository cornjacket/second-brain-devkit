# Open Questions

Unresolved design decisions for the Second Brain Developer Kit. Each item should
be resolved before the affected feature is finalized, then moved to (or
referenced from) SPEC.md as a decided convention.

---

## OQ-1: How should the golden reference repo be stored inside the devkit?

**Status:** OPEN

### Context

`second-brain-test/` is intended to be a **golden reference** — the hand-built,
known-good output of a feature — used to validate that the devkit's code
generation produces the correct result. To prevent drift, the golden reference
should live inside `second-brain-devkit/` and be version-controlled alongside the
generator code that produces it.

The complication: the feature under test relies on a **generated git repo with a
pre-commit hook** (the hook produces `*.embed.json` sidecar vectors on commit).
So the golden reference must be able to behave as a real git repo when exercised.

### The conflict

These two requirements pull in opposite directions:

1. **Stay in sync / be tracked by devkit** → the golden's files must be tracked
   by the devkit's own git.
2. **Exercise the pre-commit hook** → the golden must be (or become) a real git
   repo with a live `.git`.

A literal "repo inside a repo" (a live nested `.git`) does **not** satisfy (1):
git will not track the contents of a nested repository from the parent — it
records at most a bare submodule pointer, or ignores the directory. The result
is that the nested golden would **drift**, which defeats the entire purpose.

### Options under consideration

- **A — Plain tracked files (no live `.git`).** Store the golden's working tree
  as normal tracked files; keep the hook as a regular file (e.g.
  `golden/.githooks/pre-commit`). The test harness runs `git init` on a copy at
  test time to fire the hook. Avoids the antipattern; golden is truly tracked by
  devkit and stays in sync. The stored golden contains the *expected output*
  (notes + sidecars + hook source), which needs no committed git history to
  exist at rest.

- **B — Git submodule.** Golden remains its own real repo; devkit tracks a
  commit pointer. Preserves a literal nested repo, but adds submodule ceremony
  and "sync" means bumping pointers on every change.

- **C — Nested live `.git`.** Literal repo-inside-a-repo. Matches the mental
  model but devkit will NOT track the golden's contents, so it WILL drift.
  (Listed for completeness; appears to defeat the stated goal.)

### Decision

_Pending._
