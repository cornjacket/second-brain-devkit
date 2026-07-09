---
tags: [seed, git-automation]
---

# Commit message conventions

A commit message has a structured shape Git and tooling both rely on: a concise subject line under about fifty characters, a blank line, then a wrapped body explaining the why. Conventional Commits formalizes the subject as type(scope): summary — feat, fix, chore, refactor, docs — and marks breaking changes with a ! or a BREAKING CHANGE footer. Machine-readable commit trailers such as Signed-off-by, Co-authored-by, and Reviewed-by live in the footer block and are parsed with git interpret-trailers. Because git log, git shortlog, and release-note generators read this structure, disciplined subjects let semantic-release bump the version and assemble a changelog straight from history. A commit-msg hook can lint the message against the convention and reject a non-conforming one before it ever lands, keeping git log --oneline a clean, greppable ledger of intent.
