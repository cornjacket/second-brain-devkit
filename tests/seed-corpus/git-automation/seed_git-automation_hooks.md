---
tags: [seed, git-automation]
---

# Git hooks

Git hooks are executable scripts Git fires at defined points in the commit and push lifecycle, discovered in .git/hooks (or a shared directory pointed to by core.hooksPath). Client-side hooks include pre-commit, which runs against the staged index before the commit object is written and can abort by exiting non-zero — the standard place to run linters, formatters, and fast unit tests. The prepare-commit-msg and commit-msg hooks inspect or rewrite the message, enforcing conventional-commit format, while post-commit runs afterward for notification only and cannot veto anything. pre-push fires before refs are transmitted to the remote, letting you gate on the full test suite or block force-pushes to protected branches. Server-side pre-receive and update hooks enforce policy centrally. Because .git is never cloned, teams version hooks in-tree and wire them up with core.hooksPath or a manager like pre-commit or Husky.
