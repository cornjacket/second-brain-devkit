---
tags: [seed, ai-llm]
---

# Text embeddings

A text embedding maps a span of tokens to a dense vector in a high-dimensional latent space so that semantically related passages land near one another under cosine similarity or dot-product distance, while unrelated text spreads apart. Encoder models such as nomic-embed-text or the sentence-transformer family mean-pool their final hidden states into a fixed-width representation, often L2-normalized so cosine reduces to a dot product. These vectors power semantic retrieval, k-means clustering, deduplication, and downstream classification probes. A hard constraint is that queries and stored documents must be embedded by the same model and the same pooling — mixing checkpoints or dimensionalities makes the vectors incomparable and silently wrecks nearest-neighbor recall. Contrastive pretraining objectives pull matched query-passage pairs together and push negatives apart, which is what shapes the geometry that makes approximate nearest-neighbor indexes like HNSW return relevant neighbors.
