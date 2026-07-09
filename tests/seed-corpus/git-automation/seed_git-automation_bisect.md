---
tags: [seed, git-automation]
---

# git bisect

git bisect binary-searches the commit range between a known-good and known-bad revision to isolate the exact SHA that introduced a regression. You start the session with git bisect start, then mark endpoints with git bisect good and git bisect bad; Git checks out the midpoint commit and detaches HEAD there so you can test each candidate. Each verdict halves the suspect range, so it converges in roughly log2(N) checkouts. git bisect run <script> fully automates the hunt: Git replays the good/bad decision from the script's exit code, treating exit 125 as skip for uncompilable commits. When the first bad commit is found it prints the offending SHA, and git bisect reset restores your original branch and HEAD. It shines against a large linear history where the bug's origin is otherwise opaque.
