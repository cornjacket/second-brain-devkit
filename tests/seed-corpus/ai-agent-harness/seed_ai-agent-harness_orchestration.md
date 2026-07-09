---
tags: [seed, ai-agent-harness]
---

# Multi-agent orchestration

Orchestration coordinates several agents — pipelines, judge panels, or map-reduce fan-out — with deterministic control flow around model-driven steps. Barriers synchronize when a stage needs all prior results; pipelines avoid them when items are independent. The orchestrator, not the model, decides what runs when.
