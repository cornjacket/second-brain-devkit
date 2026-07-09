---
tags: [seed, ai-agent-harness]
---

# Planning and decomposition

Task planning has the agent decompose a high-level goal into an ordered list of concrete subtasks before it starts calling tools. A planner step emits the plan up front — often as a numbered todo list or a dependency graph where edges encode which subtask must finish before another begins — and the harness then drives execution subtask by subtask, checking each off as its stopping condition is met. Planning first prunes the search space so the tool-use loop wastes fewer actions and blows less of its step budget, and it makes progress observable: an orchestrator or a human can read the plan and see exactly where the trajectory stands. Because early plans are made under uncertainty, the agent re-plans when an observation invalidates an assumption — reordering, inserting, or dropping subtasks mid-run. Decomposition also creates clean seams for delegation, handing bounded subtasks to subagents that each pursue their own leg of the plan.
