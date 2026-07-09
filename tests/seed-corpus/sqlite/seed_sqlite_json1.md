---
tags: [seed, sqlite]
---

# JSON support

The JSON1 extension, now compiled into the amalgamation by default, parses JSON text stored in ordinary TEXT columns and exposes functions like `json_extract(col, '$.path')`, `json_valid`, `json_type`, `json_array_length`, and constructors `json_object` and `json_array`. The `->` operator returns a JSON subcomponent while `->>` returns an unquoted SQL scalar, both accepting JSONPath-style arguments. `json_each` and `json_tree` are table-valued functions that unnest arrays and objects into rows you can join against. Because extraction happens at query time, you index a hot field by declaring a generated column — `price REAL GENERATED ALWAYS AS (json_extract(doc,'$.price'))` — and building a b-tree index over it, or by creating an expression index directly on the `json_extract` call. The newer JSONB binary format stores a pre-parsed representation, skipping repeated reparsing of the text on each access.
