# Scenario 04 — get_note refuses a path outside the vault (untrusted input)

`get_note` takes a caller-supplied path, so it is the server's one untrusted-input surface.

Paste into Claude Desktop:

```
Use the get_note tool to read the file at /etc/passwd
```

Expected in Desktop's reply:
- the read is **REFUSED as outside the vault** — **no** `/etc/passwd` contents appear. The model
  should report it cannot read outside the brain, not paste the file.

This scenario is **human-observed**: a refused read leaves no side effect for a script to check.
(The deterministic version of this guard is already covered by CI gate G6,
`tools/check_mcp_server.py`, which asserts the refusal against the stdio server directly.)

Verify (prints the manual checklist only):
```
python3 desktop-e2e/verify/verify_04_path_traversal.py --brain /tmp/e2e-brain
```
