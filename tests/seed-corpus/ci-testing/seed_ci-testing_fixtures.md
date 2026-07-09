---
tags: [seed, ci-testing]
---

# Test fixtures

A fixture is the known, fixed setup a test runs against — seeded records, a temp directory, a configured client — established in a setup phase and torn down afterward so each case starts from identical conditions. In pytest a fixture is a function decorated with @pytest.fixture, its scope tunable per-function, per-module, or per-session; a yield statement splits arrange from teardown, and conftest.py shares fixtures across a directory. Factory fixtures and parametrized fixtures let one definition feed many cases. Shared fixtures cut duplication but can couple unrelated tests through mutable setup, so keep them immutable or freshly built to preserve test isolation. Prefer narrow fixtures the test actually needs over a fat god-fixture. When the expected baseline legitimately shifts, regenerate the fixture deliberately and review the resulting diff rather than letting it drift silently.
