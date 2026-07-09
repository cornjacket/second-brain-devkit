---
tags: [seed, ai-agent-harness]
---

# Evaluating agents

Agent evaluation grades whole trajectories — the ordered sequence of thought, tool call, and observation steps — rather than a single completion. Trajectory-level metrics include task success rate, steps-to-completion, tool-call accuracy, wrong-tool and malformed-argument rates, and dollar cost per rollout against a max-steps budget. A deterministic eval harness pins the scenario, mocks each tool schema's return, and replays fixed rollouts so a regression in the tool-use loop or the planner surfaces as a diff. Rubric-based grading and an LLM-as-judge score partial credit when there is no single golden trajectory, checking whether the agent decomposed the task, chose the right subagent, and hit its stopping condition. Adversarial probes and red-team suites confirm that guardrails and permission gating hold under prompt injection, and per-step traces make each failed handoff or stalled loop replayable and debuggable.
