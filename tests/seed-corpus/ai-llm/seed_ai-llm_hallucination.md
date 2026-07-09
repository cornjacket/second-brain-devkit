---
tags: [seed, ai-llm]
---

# Hallucination

A hallucination is fluent, confident output that is factually wrong or unsupported, and it is an intrinsic consequence of autoregressive decoding: the model samples the next token from a softmax over logits to maximize likelihood under its parametric memory, optimizing for plausibility rather than truth. Gaps or staleness in the pretraining corpus, high sampling temperature, and questions near the tail of the learned distribution all raise the rate. Retrieval-augmented grounding shrinks it by conditioning generation on fetched source passages instead of parametric recall, and asking for inline citations makes claims checkable. Confidence-calibrated abstention — letting the model say it does not know rather than confabulate — cuts unsupported assertions, and lower temperature narrows the distribution toward higher-likelihood continuations. Because the model has no built-in mechanism to verify facts against ground truth, downstream claims should be checked against an authoritative source before being acted on.
