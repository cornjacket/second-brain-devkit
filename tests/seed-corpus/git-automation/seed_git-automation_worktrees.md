---
tags: [seed, git-automation]
---

# Worktrees

git worktree lets a single repository check out several branches simultaneously into distinct working directories, all backed by one shared object database and one set of refs. git worktree add ../hotfix release/2.1 spins up a linked worktree with its own working tree, its own index, and its own detached or attached HEAD, so you switch context without git stash or a second clone. Because the object store is shared, fetches, commits, and packs are visible across every worktree, but Git enforces that no two worktrees check out the same branch at once to prevent conflicting ref updates. It suits running a long build on one branch while coding on another, reviewing a pull-request branch beside your feature work, or bisecting in isolation. git worktree list enumerates them, and git worktree prune reclaims administrative metadata after a linked directory is deleted.
