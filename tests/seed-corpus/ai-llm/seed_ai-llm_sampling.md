---
tags: [seed, ai-llm]
---

# Temperature and sampling

Decoding turns the model's next-token distribution into text; temperature scales that distribution, with low values near-deterministic and high values more varied. Top-p (nucleus) and top-k sampling truncate the tail to avoid incoherent tokens. Lower temperature suits extraction and code; higher suits brainstorming.
