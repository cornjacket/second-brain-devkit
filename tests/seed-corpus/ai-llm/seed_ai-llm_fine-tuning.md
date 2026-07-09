---
tags: [seed, ai-llm]
---

# Fine-tuning vs prompting

Fine-tuning updates a base model's weights on task-specific data, while prompting steers a frozen model at inference time. Parameter-efficient methods like LoRA adapt a small number of extra weights instead of the full network. Prefer prompting or retrieval first; fine-tune only when behavior must be baked in.
