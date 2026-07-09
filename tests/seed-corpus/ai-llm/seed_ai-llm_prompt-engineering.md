---
tags: [seed, ai-llm]
---

# Prompt engineering

Prompt engineering shapes a frozen model's behavior entirely through the tokens placed in its context window, exploiting in-context learning rather than any weight update. A system prompt sets persona and constraints, few-shot exemplars demonstrate the target input-output mapping so the model infers the pattern, and explicit output-format instructions or a JSON schema constrain the shape so downstream parsing stays deterministic. Chain-of-thought prompting elicits intermediate reasoning tokens before the final answer, which measurably lifts arithmetic and multi-step tasks; self-consistency samples several reasoning traces and takes a majority vote, while zero-shot triggers like "let's think step by step" approximate the effect without exemplars. Delimiters, role tags, and negative instructions reduce ambiguity, and careful ordering matters because the model attends unevenly across the window. Prompts are brittle across model versions and sampling settings, so treat them as versioned artifacts and evaluate revisions against a fixed test set.
