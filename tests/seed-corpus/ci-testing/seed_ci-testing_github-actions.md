---
tags: [seed, ci-testing]
---

# GitHub Actions

GitHub Actions executes workflows defined in YAML under .github/workflows, triggered by repository events through the on: key — push, pull_request, workflow_dispatch, or a cron schedule. A workflow declares jobs, and each job runs on a hosted or self-hosted runner, moving through ordered steps that either run a shell command via run: or invoke a reusable action via uses:, like actions/checkout or actions/setup-python. Jobs run in parallel by default unless chained with needs:, and a strategy.matrix fans one job across Python versions and operating systems to form the build matrix. actions/cache keys dependency directories to skip reinstalls, secrets flow through the secrets context, and permissions scope the GITHUB_TOKEN. Reusable and composite workflows factor out duplication, while status checks report each job back onto the pull request to gate the merge.
