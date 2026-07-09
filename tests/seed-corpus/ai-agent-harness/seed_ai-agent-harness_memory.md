---
tags: [seed, ai-agent-harness]
---

# Agent memory

Because a context window is finite and a long trajectory would overflow it, an agent harness externalizes working memory rather than carrying the whole transcript forward. Short-term working memory is the agent scratchpad — the running record of thought, action, and observation steps for the current task, plus intermediate results a plan needs — which the harness can prune, summarize, or compact when the loop grows long. Durable long-term memory lives outside the prompt in files, a key-value store, or a vector index the agent writes to and later retrieves from on demand, so a conclusion from an earlier session or a sibling subagent can be recalled without replaying it. Recall quality hinges on how memories are chunked and indexed and on when the retrieval step fires in the loop. Handoffs between orchestrated agents pass distilled memory — each subagent's conclusion, not its full scratchpad — keeping the parent's working memory clean.
