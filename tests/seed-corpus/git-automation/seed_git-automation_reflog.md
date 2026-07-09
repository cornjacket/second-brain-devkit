---
tags: [seed, git-automation]
---

# The reflog

The reflog is a per-repository journal of every movement of HEAD and each branch ref, recording the old and new SHA for every commit, checkout, reset, rebase, merge, and cherry-pick. Unlike the commit graph it is local-only and never pushed. You inspect it with git reflog or git reflog show <ref>, addressing entries by the HEAD@{n} or HEAD@{2.hours.ago} syntax. Its great use is recovery: after a git reset --hard or a botched rebase leaves commits unreachable from any branch, the reflog still names their SHAs, so git reset --hard HEAD@{1} or git branch rescue <sha> resurrects them before garbage collection prunes dangling objects. Entries expire per gc.reflogExpire (ninety days for reachable, thirty for unreachable) after which git gc can reap them. It is the definitive undo net for local history rewrites.
