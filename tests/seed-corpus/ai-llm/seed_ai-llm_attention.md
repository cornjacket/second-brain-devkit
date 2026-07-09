---
tags: [seed, ai-llm]
---

# The attention mechanism

Self-attention projects each token embedding into query, key, and value vectors, then scores every query against every key with a scaled dot product before a softmax turns those logits into attention weights over the sequence. The weighted sum of value vectors yields a context-aware representation that captures long-range dependencies without recurrence. Multi-head attention splits the model dimension across several heads so distinct attention heads specialize on different relationships — syntactic agreement, coreference, positional adjacency — and their outputs are concatenated and projected back. Causal masking zeroes out future positions so a decoder attends only leftward during autoregressive generation. Because the score matrix is quadratic in sequence length, much transformer research targets sparse, linear, or grouped-query attention and rotary positional encoding to stretch the context window while keeping the residual stream stable across stacked layers.
