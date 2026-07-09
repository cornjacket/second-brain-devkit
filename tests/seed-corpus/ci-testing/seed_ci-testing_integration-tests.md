---
tags: [seed, ci-testing]
---

# Integration tests

An integration test exercises several components wired together across a real boundary — a service talking to its database, a handler calling a downstream API, or a chain of modules passing objects between layers — rather than one unit in isolation. Its scope is broader than a unit test, so it catches the failures unit tests structurally cannot: schema drift, serialization mismatches, misconfigured connection strings, broken migrations, and contract violations between a producer and a consumer. Because it stands up real collaborators, teams spin them under ephemeral Docker containers or Testcontainers, seed a throwaway database in setup, and tear it down afterward to keep each run isolated. These tests run slower and are more prone to flakiness from timing and shared state, so the test pyramid keeps them fewer than the unit layer, reserving them for the seams where genuine wiring bugs hide.
