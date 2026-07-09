---
tags: [seed, sqlite]
---

# sqlite-vec

sqlite-vec is a loadable extension, successor to sqlite-vss, that registers a `vec0` virtual-table module for storing and searching dense embeddings next to relational rows. You declare `CREATE VIRTUAL TABLE items USING vec0(embedding float[768])`, insert vectors as JSON arrays or packed float32 blobs, and run a k-nearest-neighbor query with `WHERE embedding MATCH :query AND k = 10 ORDER BY distance`, choosing the metric — cosine, L2, or L1 — at column declaration. It also exposes scalar helpers like `vec_distance_cosine`, `vec_normalize`, and `vec_quantize_binary` for bit-packed vectors, plus partitioning and metadata-column filters to prune the KNN scan. Loading requires an extension-enabled build via `sqlite3_load_extension`, the `.load` dot-command, or the apsw connector, since Python's bundled module often disables extension loading. Keeping embeddings in the same file makes a second brain self-contained, with no external vector database to run alongside it.
