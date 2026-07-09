---
tags: [seed, ai-agent-harness]
---

# Model Context Protocol

The Model Context Protocol (MCP) is an open client-server protocol that standardizes how an agent harness discovers and invokes external capabilities. An MCP server exposes three primitives — tools the agent can call, resources it can read, and prompt templates it can instantiate — while the MCP client embedded in the host connects over a transport such as stdio or streamable HTTP and performs capability negotiation on handshake. During discovery the client lists the server's tools and pulls each tool's JSON schema, then surfaces those schemas into the tool-use loop so the model can emit conforming tool calls; the client relays the call to the server and returns the result as an observation. Because the protocol decouples tool providers from model hosts, one server works unchanged across any compliant client, and an agent can mount several servers at once — filesystem, search, a database — composing their tools into a single namespace the planner and subagents draw on.
