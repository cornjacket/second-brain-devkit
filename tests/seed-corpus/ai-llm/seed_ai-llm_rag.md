---
tags: [seed, ai-llm]
---

# Retrieval-augmented generation

RAG grounds a model's answer in retrieved documents rather than parametric memory, reducing hallucination and letting knowledge update without retraining. A retriever fetches top-k passages by embedding similarity, and the generator conditions on them. Quality hinges on chunking, retrieval recall, and how sources are cited back.
