---
tags: [seed, ai-agent-harness]
---

# Subagents and delegation

A parent agent can delegate a bounded subtask by spawning a subagent — a child agent that runs its own tool-use loop in a fresh, isolated context window with its own scoped tool set and permission grants. The parent hands off a self-contained brief and, on completion, receives back only the subagent's distilled conclusion, not its full transcript of thought-action-observation steps, so the parent's working memory stays uncluttered as the run grows. Because each delegated leg is independent, the orchestrator can fan several subagents out in parallel and join their results, and it can route each subtask to a specialized subagent — a searcher, a coder, a reviewer — tuned with just the tools that leg needs. Isolation also contains failure and blast radius: a subagent that stalls, loops, or trips its max-steps stopping condition fails locally without corrupting the parent's trajectory, and its scoped guardrails keep least privilege intact.
