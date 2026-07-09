---
tags: [seed, git-automation]
---

# Submodules

A submodule nests one Git repository inside another at a precisely pinned commit, keeping the child's object database and history fully separate from the superproject's. The parent does not vendor the child's files; instead it stores a gitlink — a special tree entry recording the exact child SHA — plus a .gitmodules file mapping each submodule path to its upstream URL and tracking branch. You initialize and fetch nested content with git submodule update --init --recursive, and cloning a superproject needs --recurse-submodules or the submodule directories arrive empty. Advancing a submodule means checking out a new commit inside it and then committing the updated gitlink in the parent, which is why they add coordination overhead: contributors forget to push the child first, leaving the superproject pointing at an unfetchable SHA. Use them deliberately for genuinely independent, versioned dependencies.
