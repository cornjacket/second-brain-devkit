---
tags: [seed, git-automation]
---

# Rebase vs merge

Rebase and merge are two ways to integrate divergent branches. git rebase replays your branch's commits one at a time onto a new base tip, rewriting each into a fresh SHA and producing a linear history with no merge commit; when the upstream is an ancestor the integration collapses to a fast-forward. git merge instead records a merge commit with two parents, preserving the true branch topology and the original SHAs. Interactive rebase, git rebase -i, opens a todo list where you pick, squash, fixup, reword, drop, or reorder commits to curate a branch before opening a pull request. Because rebasing rewrites history, never rebase commits already pushed and pulled by others — you would force a divergent history requiring --force-with-lease. Conflicts pause the rebase per commit; resolve, git add, then git rebase --continue, or bail with --abort.
