---
tags: [seed, ai-agent-harness]
---

# Model Context Protocol

MCP is an open protocol that exposes tools, resources, and prompts from a server to an AI client over a standard transport like stdio. It decouples tool providers from model hosts so the same server works across clients. Each tool advertises a JSON schema the model calls against.
