---
tags: [seed, ci-testing]
---

# Mocks and stubs

A test double is any object substituted for a real collaborator so the unit under test runs in isolation. The taxonomy is precise: a stub returns canned values for the calls the test needs; a fake is a lightweight working implementation like an in-memory repository; a spy records how it was invoked so the test can inspect the call log afterward; and a mock carries preprogrammed expectations and fails the assertion if those calls never arrive. Frameworks like unittest.mock supply MagicMock, patch to swap a dependency at import time, return_value and side_effect to script behavior, and assert_called_once_with to verify interactions. Doubles shield the unit from slow, networked, or nondeterministic collaborators and keep tests fast and hermetic. But over-mocking couples the test to internal call sequences, so it verifies the mock's choreography instead of real behavior and breaks on every harmless refactor.
