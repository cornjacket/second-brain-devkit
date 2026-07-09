---
tags: [seed, ci-testing]
---

# Test-driven development

Test-driven development inverts the usual order: you write a failing test that pins down the desired behavior before any implementation exists, watch it go red, write the minimal production code to make it pass and turn the bar green, then refactor with the test as a safety net. This red-green-refactor loop runs in tight cycles, adding one small assertion at a time so the design grows only what the tests demand and scope creep stays honest. Writing the test first forces you to design the unit's interface from the caller's side, which pressures the code toward smaller, injectable, testable seams and discourages hidden coupling. The accumulated suite doubles as an executable specification and a regression guard: it documents intent in runnable form and catches breakage on every commit. A disciplined practitioner never writes production code without a failing test justifying it first.
