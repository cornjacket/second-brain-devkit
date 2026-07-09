---
tags: [seed, ai-llm]
---

# Text embeddings

An embedding maps text to a dense vector so that semantically similar passages land close together under a distance metric like cosine. Models such as nomic-embed-text produce fixed-width vectors used for retrieval, clustering, and classification. The same model must embed both stored documents and queries or the vectors are not comparable.
