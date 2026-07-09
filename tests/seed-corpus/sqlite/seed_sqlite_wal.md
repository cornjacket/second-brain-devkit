---
tags: [seed, sqlite]
---

# Write-ahead logging

WAL mode writes changes to a separate log first, letting readers continue against the old database while a writer appends. It improves concurrency over the default rollback journal. A checkpoint later folds the log back into the main file.
