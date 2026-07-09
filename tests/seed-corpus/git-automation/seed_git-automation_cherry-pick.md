---
tags: [seed, git-automation]
---

# Cherry-pick

git cherry-pick <sha> replays the diff introduced by a single commit onto the tip of the current branch, minting a brand-new commit with a fresh SHA but the same authored patch and message. Because it copies one change rather than reachability, it is the standard tool for backporting a hotfix from main onto a maintenance or release branch without dragging along unrelated history. You can cherry-pick a range with A..B, and -x appends a "(cherry picked from commit …)" trailer for provenance. When the patch does not apply cleanly Git pauses with conflict markers in the index exactly like a small merge; you resolve, git add the files, and finish with git cherry-pick --continue, or abandon with --abort. Duplicating commits this way can create equivalent-but-distinct SHAs that later confuse merge and rebase, so prefer it for isolated fixes.
