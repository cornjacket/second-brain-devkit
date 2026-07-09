---
tags: [seed, ai-agent-harness]
---

# The tool-use loop

An agent harness runs a loop: the model proposes a tool call, the harness executes it, feeds the result back, and repeats until the model emits a final answer. The harness owns execution, not the model, so it enforces permissions and timeouts. Clear tool schemas and error feedback keep the loop from stalling.
