# Inbox — messages for the next session (task #64)

**`vault/inbox.md` is where a brain's owner leaves messages for the next agent session.**
"File this article as a note." "The CSET date moved to March." "Check whether the permit email
came." Things to get done, but not now.

## Why it exists

It came from a real brain. The owner asked whether there was an inbox for leaving the repo
messages, and found two folders named `inbox` that did other things. One was the PDF drop
folder, since renamed `vault/pdf-inbox/` (#61). The other was the task system's `inbox/` of raw
ideas. Neither was a message queue, and nothing told an agent to look at either one at the
start of a session.

## The design

| Decision | Choice | Why |
| --- | --- | --- |
| Where | vault root, beside `dashboard-index.md` | Outside every PARA root, so it is never embedded. A message is an instruction, not knowledge: once handled it is gone, and a vector of "do X tomorrow" would compete against real notes. Same reasoning as the dashboard ([dashboard-index.md](dashboard-index.md)). |
| Format | `- YYYY-MM-DD: text` lines under `## Messages` | Writable from any editor, Obsidian, or a phone with git. No tool is needed to leave a message. |
| Who reads it | every agent session, first | The emitted `CLAUDE.md` block says to read it before anything else. A message nobody is told to read is worse than no inbox, because the owner believes it was delivered. |
| What happens to a message | done if small, otherwise turned into a note, a project checkbox or a dashboard row; then the line is **deleted** in the same commit | **A queue, not a log.** Git keeps the history, and a list of done items is noise the next session must read past. A message that cannot be handled yet stays, with a reason appended, so it is not retried blind. |
| Delivery | `VAULT_SEEDED`: created if absent, never overwritten | It holds the owner's waiting messages, so it has the dashboard's rule and its two silent failures: an upgrade that clobbers messages, and an older brain that never receives the file. |
| Visibility | `doctor.py` prints `inbox: N message(s) waiting` | Information, not a problem. A full inbox is the feature working, and `--repair` cannot read one. The seed's own explanatory bullets sit under other headings, so a fresh brain reports `inbox empty`. |

Encrypted brains do not get the seed. `VAULT_SEEDED` skips them, as it does for the dashboard:
the vault is the user's alone, so they create the file themselves if they want it.

## Not built (yet)

- **No MCP tool.** Claude Desktop cannot append to the inbox. Leaving a message from Desktop or
  a phone without git would need an `add_inbox_message` tool, which is the obvious next step
  if the inbox gets used.
- **No session-start hook.** The read-first rule lives in `CLAUDE.md`, which every session
  loads. A hook would make it mechanical, but it would tie the brain to one agent's hook
  system.

## What is gated

Gate 28, `tools/check_inbox.py`, checks that:

- a fresh brain has the file and it matches the seed
- `doctor.py` reports the fresh inbox as empty and counts one waiting message
- an upgrade leaves a waiting message byte-for-byte and never reports the file `CHANGED`
- a brain that lacks the file receives it
- it is not an embeddable note
- the emitted `CLAUDE.md` tells an agent to read it first
- the vendored `test_inbox.py` suite passes

Mutation-tested: moving the inbox from `VAULT_SEEDED` to `VAULT_OWNED` turns four assertions red.
