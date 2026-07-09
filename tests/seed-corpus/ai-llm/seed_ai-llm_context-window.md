---
tags: [seed, ai-llm]
---

# The context window

The context window is the maximum number of tokens a model can attend to at once, spanning the system prompt, conversation, retrieved context, and the reply. Overflowing it forces truncation or summarization. Long windows help but attention still degrades on distant tokens, so placement of key information matters.
