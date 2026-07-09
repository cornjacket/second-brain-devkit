---
tags: [seed, ai-agent-harness]
---

# The ReAct pattern

The ReAct (reason-then-act) pattern structures each turn of the agent loop as an explicit Thought, Action, Observation triple: the model reasons about what to do next, emits an action as a concrete tool call, and then reads the harness-supplied observation before reasoning again. Interleaving a written reasoning trace with acting — rather than deciding silently — lets the model condition each tool selection on the freshly returned result, so the trajectory self-corrects when an observation contradicts its expectation. The scaffolding usually enforces the format with a stop sequence after Action, dispatches the tool, appends the Observation to the scratchpad, and re-prompts, iterating until the model emits a Final Answer or trips the max-steps cap. Because every Thought is recorded, a stalled or wrong-tool run is legible and debuggable step by step. ReAct spends extra reasoning tokens per step to buy markedly steadier multi-step tool use, and it pairs naturally with up-front planning and re-planning.
