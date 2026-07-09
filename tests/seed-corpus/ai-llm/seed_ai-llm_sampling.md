---
tags: [seed, ai-llm]
---

# Temperature and sampling

Decoding turns the model's next-token probability distribution into text, one token at a time in an autoregressive loop. At each step the transformer emits raw logits over the vocabulary; temperature divides those logits before the softmax, so values below one sharpen the distribution toward the argmax and near-deterministic greedy output, while values above one flatten it and raise diversity and surprise. Top-k sampling restricts the candidate pool to the k highest-probability tokens, and top-p (nucleus) sampling instead keeps the smallest set whose cumulative probability mass exceeds p, truncating the long incoherent tail adaptively. Min-p, repetition and frequency penalties, and beam search are further knobs, and beam search trades diversity for likelihood on constrained tasks. Low temperature with tight top-p suits extraction, classification, and code where fidelity matters; higher temperature widens the distribution for brainstorming and creative generation. These sampling parameters, not the weights, govern the stochasticity of every completion.
