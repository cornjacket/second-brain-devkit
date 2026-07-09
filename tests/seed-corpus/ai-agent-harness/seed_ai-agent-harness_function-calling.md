---
tags: [seed, ai-agent-harness]
---

# Function calling

Function calling lets the model emit a structured tool call — a function name plus a JSON arguments object validated against a declared tool schema — instead of free text. The harness advertises each tool's schema, its parameter types, required fields, and enums, then parses the model's proposed call, validates the arguments, dispatches to the real function, and threads the return back into the transcript as a tool-result message the model reads on the next turn. When arguments fail schema validation the harness rejects the call and feeds the validation error back so the model can repair and retry, rather than crashing the tool-use loop. Parallel tool calls let one turn fan out several invocations at once. Crisp schema descriptions, tight enums, and worked argument examples steer tool selection and cut malformed-argument and wrong-tool rates across the loop.
