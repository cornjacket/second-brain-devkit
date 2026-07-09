---
tags: [seed, git-automation]
---

# Triggering CI

Continuous-integration pipelines subscribe to repository events — push, pull_request, and tag creation — and dispatch a workflow run against the pushed refs. On GitHub Actions the workflow YAML declares on: triggers with branches, tags, and paths filters so a run fires only when the relevant refs or files change, sparing noise on docs-only commits. Each job checks out the commit SHA that triggered it, runs the build and test matrix, and reports a status check keyed to that SHA. Branch-protection rules mark those checks as required, so a pull request cannot merge or fast-forward until every check is green and the branch is up to date with the base. Concurrency groups cancel superseded runs when new commits land, and pull_request_target versus pull_request governs whether forked-PR runs get repository secrets.
