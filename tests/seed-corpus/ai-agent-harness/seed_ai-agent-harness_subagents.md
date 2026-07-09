---
tags: [seed, ai-agent-harness]
---

# Subagents and delegation

A parent agent can spawn subagents to handle bounded subtasks in parallel, each with its own context window and tools. Delegation keeps the parent's context clean and lets independent work fan out. The parent keeps only each subagent's conclusion, not its full transcript.
