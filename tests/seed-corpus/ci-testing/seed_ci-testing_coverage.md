---
tags: [seed, ci-testing]
---

# Code coverage

Code coverage instruments the suite as the test runner executes it, recording which lines, branches, and statements were reached. Line coverage counts executed source lines; branch coverage tracks whether both arms of each conditional were taken; statement coverage sits between them. Tools like coverage.py, JaCoCo, and Istanbul emit an lcov or Cobertura report the CI job uploads as a build artifact. Teams gate merges on a coverage threshold — say eighty percent branch coverage — and fail the pipeline when a pull request drops below it or leaves a diff line uncovered. But high coverage never proves correctness: a test can execute a code path without a single assertion, inflating the number while catching no regression. Read the report to hunt untested branches and error handlers, not to chase a percentage you can game with vacuous tests.
