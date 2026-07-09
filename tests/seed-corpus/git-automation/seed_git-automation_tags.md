---
tags: [seed, git-automation]
---

# Tags and releases

A tag is a named ref pointing at a single commit, and Git offers two kinds. A lightweight tag is merely a pointer under refs/tags, whereas an annotated tag, created with git tag -a, is a full tag object in the object database carrying a tagger identity, a timestamp, a message, and optionally a GPG signature from git tag -s for verifiable provenance. Annotated tags are the convention for releases because they are dated, attributed, and signable. Semantic-version tags like v1.2.0 following MAJOR.MINOR.PATCH drive release automation: pushing a matching tag with git push origin v1.2.0 fires a tag-triggered CI workflow that builds artifacts and cuts a GitHub Release. git describe walks back to the nearest annotated tag to synthesize a version string. Unlike branches, tags are immutable pointers that never advance with new commits.
