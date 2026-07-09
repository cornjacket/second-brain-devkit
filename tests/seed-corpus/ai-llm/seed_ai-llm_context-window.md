---
tags: [seed, ai-llm]
---

# The context window

The context window is the maximum span of tokens the transformer can attend to in a single forward pass, and every token counts against it — the system prompt, the running conversation, any retrieved passages, and the generated continuation all share the same budget. Positional encoding, whether learned or rotary, determines how far the model can extrapolate beyond the sequence lengths seen during pretraining before coherence collapses. Overflowing the window forces truncation, sliding-window eviction, or recursive summarization of earlier turns. Even within a long window the attention distribution thins over distant tokens, producing the lost-in-the-middle effect where facts buried mid-context are recalled worse than those at the head or tail. This makes token budgeting and the placement of load-bearing instructions a real determinant of output quality, and it directly bounds the key-value cache the model must hold in memory during decoding.
