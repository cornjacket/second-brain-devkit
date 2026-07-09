---
tags: [seed, ai-llm]
---

# Retrieval-augmented generation

Retrieval-augmented generation grounds a model's answer in documents fetched at inference time rather than in the parametric memory frozen at pretraining, which curbs hallucination and lets the knowledge base update without any retraining or fine-tuning. The pipeline chunks a corpus into passages, embeds each with an encoder model, and stores the vectors in an index; at query time the retriever embeds the question and pulls the top-k passages by cosine similarity, often over an approximate nearest-neighbor structure like HNSW. Those passages are concatenated into the prompt so the generator conditions its decoding on them and can cite sources back. Answer quality hinges on chunk size and overlap, retrieval recall and precision, and reranking a cross-encoder applies over the initial candidates. Hybrid retrieval blends dense embeddings with sparse BM25 lexical matching, and everything must fit the context window, so retrieved tokens compete with the instructions for budget.
