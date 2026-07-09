---
tags: [seed, sqlite]
---

# Full-text search with FTS5

FTS5 is a built-in virtual-table module that maintains an inverted index over tokenized documents and ranks matches with its BM25 implementation exposed through the `rank` column and the `bm25()` auxiliary function. You declare the table with `CREATE VIRTUAL TABLE docs USING fts5(title, body)` and query it with the MATCH operator, supporting prefix tokens, NEAR proximity queries, column filters, and boolean AND/OR/NOT expressions. The `porter` and `unicode61` tokenizers fold case and stem terms; `snippet()` and `highlight()` return excerpts around hits. A `content=''` contentless or external-content table stores only the index and references rowids in the base table, saving space. The shadow tables (`docs_data`, `docs_idx`, `docs_docsize`) hold the segment b-trees, and `INSERT INTO docs(docs) VALUES('optimize')` merges segments. FTS5 catches exact-term lexical matches that dense vector retrieval overlooks.
