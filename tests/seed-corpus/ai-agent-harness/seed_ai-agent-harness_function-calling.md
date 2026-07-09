---
tags: [seed, ai-agent-harness]
---

# Function calling

Function calling lets a model request a structured call — a name plus JSON arguments validated against a schema — instead of free text. The harness runs the function and returns the result for the model to use. Schema validation with retries keeps arguments well-formed.
