---
tags: [seed, ai-agent-harness]
---

# Guardrails and permissions

Guardrails constrain what the agent may do at each turn of the tool-use loop. Permission gating sits between the model's proposed tool call and its execution: an allow-list and deny-list decide which tools and which argument patterns are admissible, and irreversible or destructive actions — writes, deletes, spend, shell exec — trip a human-in-the-loop approval prompt before the harness dispatches. Least-privilege scoping hands each agent and each subagent only the tools its subtask needs, so a compromised or manipulated trajectory has a small blast radius. Sandboxing isolates code execution and file access; input filters screen for prompt injection riding in tool observations before it reaches the model. Defense in depth layers these controls so no single check is load-bearing, and every gated decision is logged to the trajectory for later audit and adversarial evaluation of whether the guardrails actually held.
