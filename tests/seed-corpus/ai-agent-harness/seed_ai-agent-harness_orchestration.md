---
tags: [seed, ai-agent-harness]
---

# Multi-agent orchestration

Multi-agent orchestration coordinates several specialized agents under a top-level orchestrator that owns the control flow while each agent owns its model-driven turns. Common topologies include the sequential pipeline, where one agent's output is the next agent's input; map-reduce fan-out, where the orchestrator spawns worker subagents over independent shards and a reducer merges their conclusions; and judge or debate panels, where multiple agents propose and a critic adjudicates. Handoffs pass a scoped brief and the relevant slice of working memory from one agent to the next, so a routing agent can delegate a subtask to the specialist best equipped for it. Barriers synchronize a stage that needs every prior worker's result before proceeding; independent items skip the barrier and stream through the pipeline. Crucially the deterministic orchestrator, not any single model, decides which agent runs when, enforces max-steps and stopping conditions across the whole run, and threads guardrails through every handoff.
