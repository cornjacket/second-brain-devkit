---
tags: [seed, sqlite]
---

# sqlite-vec

sqlite-vec is an extension that adds vector search via vec0 virtual tables, storing embeddings alongside relational data and answering k-nearest-neighbor queries by cosine or L2 distance. It keeps a brain local and dependency-light — no separate vector database. Loading it needs an extension-capable SQLite build or the apsw connector.
