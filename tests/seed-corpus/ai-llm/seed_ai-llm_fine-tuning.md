---
tags: [seed, ai-llm]
---

# Fine-tuning vs prompting

Fine-tuning updates a pretrained base model's weights by continuing gradient descent on task-specific supervised examples, whereas in-context prompting steers a frozen checkpoint purely at inference time through the tokens in the context window. Full fine-tuning rewrites all parameters and risks catastrophic forgetting of the base capabilities, so parameter-efficient methods dominate in practice: LoRA freezes the original weights and trains low-rank adapter matrices injected into the attention and feed-forward projections, and QLoRA does the same over a 4-bit quantized backbone to fit on modest GPUs. Supervised fine-tuning on instruction pairs is often followed by preference alignment such as RLHF or DPO to shape tone and refusals. The usual heuristic is to exhaust few-shot prompting and retrieval-augmented grounding first, then reach for a LoRA adapter only when a behavior, format, or domain vocabulary must be baked into the weights rather than re-specified every request.
