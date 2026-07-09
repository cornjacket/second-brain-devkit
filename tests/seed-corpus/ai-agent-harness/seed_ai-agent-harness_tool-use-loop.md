---
tags: [seed, ai-agent-harness]
---

# The tool-use loop

The tool-use loop is the beating heart of an agent harness. On each iteration the model proposes a tool call — a function name and JSON arguments — the harness validates it against the tool schema, dispatches to the real tool, captures the return, and appends it to the transcript as an observation the model reads on its next turn; the loop repeats until the model emits a final answer or trips a stopping condition. Critically the harness, not the model, owns execution, so it is the enforcement point for permission gating, argument validation, timeouts, and rate limits on every call. It also decides when to halt: a max-steps cap and a budget guard prevent runaway loops, and a no-progress detector breaks cycles where the model repeats the same failing action. Clean tool schemas, actionable error feedback fed back as observations, and retry-on-invalid-arguments keep the loop from stalling and let the trajectory recover instead of dead-ending.
