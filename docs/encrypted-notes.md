# Encrypted notes at rest (task #42)

A brain backed by a git remote pushes every note, in the clear, to a server you do
not own. This feature makes the committed form of a brain unreadable — **bodies and
filenames both** — while the working tree stays exactly as it is today: plaintext
`.md` files that Obsidian opens, `search_vault.py` searches, and the embedder embeds.

**Encryption is a git-layer concern, not a note-layer one.** Nothing about how a note
is written, embedded, linked or searched changes. What changes is what git is allowed
to see.

Off by default. A brain that never enables it is byte-identical to today's.

## Threat model

**Protects against:** anyone who can read the remote — the hosting provider, a
mis-set repository visibility, a stolen laptop backup of the `.git` directory, a
future breach of a service that has your repo today.

**Does not protect against:** anything with access to your unlocked working tree.
The plaintext is right there, and it must be — the whole brain reads it.

**Still visible in the committed form**, and stated here rather than discovered later:

- the **number** of notes, and the size of each ciphertext (a long note is visibly long)
- commit **timestamps** and their cadence
- the four PARA directory names and the devkit's own docs — identical in every brain,
  so they say nothing about you
- **anything already pushed before you switched it on.** Enabling encryption does not
  reach back into history. Plaintext in an existing remote stays there until the
  history is rewritten, and the migration says so before it starts.

Ciphertext **size padding** is deliberately out of scope for #42; it is recorded here
so the gap reads as a decision rather than an oversight.

## What is content, and what is machinery

The set of encrypted files is not a hand-maintained list. It follows one rule, which
is already implemented in `tools/update_brain.py:126`:

> **If `update_brain.py` may overwrite it, it is machinery and stays plaintext.
> Otherwise it is content and gets encrypted.**

An upgrade must never need your passphrase, and anything the devkit is free to
overwrite is by construction identical in every brain — so it carries no information
about you.

| Encrypted (content) | Plaintext (machinery) |
| --- | --- |
| `vault/**/*.md` — every PARA note and every `vault/glossary/<term>.md` | `README.md`, `CLAUDE.md`, `GEMINI.md`, `GLOSSARY.md` |
| | `vault/templates/new-note.md` — the one carve-out inside the vault |
| | `skill/`, `desktop-e2e/`, `seeds/`, `tests/fixtures/` |

`vault/templates/new-note.md` is forced, not chosen: it is `update_brain.py`'s single
`VAULT_OWNED` path, `templates/` is not a PARA root so it is never embedded or
searched, and **CI gate 9 requires it to match `CLAUDE.md` byte-for-byte** — encrypting
it would put a build-time invariant behind a passphrase.

`GLOSSARY.md` is documentation *about* the glossary layer, not a note in it. It ships
with no terms and is byte-identical across the template and every brain checked; the
vocabulary itself is one note per term under `vault/glossary/`, which **is** encrypted.

**The rule is enforced, not remembered.** A gate computes the classification from
`update_brain.py`'s own preserve logic and fails if an emitted Markdown file lands in
neither bucket — so a new file cannot ship without a classification, and forgetting is
a build error instead of a leak found on someone's remote. The same gate flags
`GLOSSARY.md` the moment it stops matching the template, which is exactly the moment it
would have started being content.

## Layout

Working tree (yours, plaintext, git-ignored):

```
vault/projects/kitchen-remodel.md
vault/glossary/retrieval-substrates.md
```

What git tracks:

```
enc/JBSWY3DPEHPK3PXPKRUG.md.enc
enc/KRUGKIDROVUWG2ZAMJSW.md.enc
enc/keyfile.json
```

Extension `.md.enc`, not `.mdx`: `.mdx` is a real format in the wild (Markdown + JSX)
and every editor would mis-highlight it, and the double extension keeps the ignore rule
an **exact** glob — `*.md` does not match `foo.md.enc`, so nothing depends on negation
ordering.

### The encrypted name

```
name = base32( HMAC-SHA256(k_name, "vault/projects/kitchen-remodel.md") )[:20]
```

**Keyed**, so nobody without the passphrase can test whether this brain contains
`salary-negotiation.md`. **Deterministic**, so an unchanged note keeps its name commit
after commit and produces no diff. **Not reversible** — and it does not need to be,
because the path travels inside the file.

**Flat, not mirrored.** `enc/projects/<opaque>` would still leak PARA bucket membership
and every subfolder name you chose. The encrypted tree is a bag of blobs.

Cost: git rename tracking and `git log -- <one note>` no longer work by path.
`scripts/encrypt_vault.py --name-of <path>` and `--path-of <name>` bridge it locally.

### The envelope

The header is prefixed to the note **before** encryption and stripped **after**
decryption, so the restored file is byte-identical to what you wrote. It never touches
the disk in plaintext:

```json
{"v":1, "path":"vault/projects/kitchen-remodel.md", "phash":"<HMAC of plaintext>"}
```

Restoring the whole brain is then: for each `enc/*.md.enc`, decrypt, read `path` from
the header, write the body there.

**`phash` prevents churn.** AES-GCM uses a random nonce, so re-encrypting an unchanged
note would produce different bytes and re-diff every note on every commit. The
encryptor compares the plaintext's HMAC against the header's and **skips a note whose
substance is unchanged** — the same skip-gate shape the embed path already uses for
`content_hash`.

### Why not a manifest

A single `enc/manifest` mapping name → path is the obvious design, and it is rejected:
every commit rewrites it, so on a two-machine brain (the `--remote` setup already
shipped) two independent note additions conflict *every time* — and since it is
ciphertext, git cannot merge it, leaving you to resolve blind. Lose or corrupt it and
every blob becomes unidentifiable at once.

Per-file headers give the same mapping with no shared mutable state: a conflict happens
only when the same note changed in both places, which is a real conflict, and one
damaged blob costs one note.

Orphans and renames are handled by a sweep — after encrypting, decrypt just the headers
in `enc/` and drop any blob whose `path` no longer exists.

## Crypto

- **KDF:** `hashlib.scrypt` (stdlib), `n=2**17, r=8, p=1`, 16-byte salt from
  `enc/keyfile.json`. Deliberately slow: see "brute force" below.
- **Cipher:** AES-256-GCM via `cryptography` (`AESGCM`), a fresh random 12-byte nonce
  per encryption, the whole envelope authenticated.
- **Sub-keys** derived from the scrypt output by HKDF, one each for `k_enc`, `k_name`,
  `k_hash`, `k_verify` — never the same key for two purposes.

`cryptography` is an **optional dependency** in `requirements-crypt.txt`, exactly the
`pypdf` / `requirements-pdf.txt` precedent: a brain that never enables encryption never
installs it. Python's stdlib has no AES, and rolling one is not on the table.

*Rejected: shelling out to `age`.* No Python dependency and a well-reviewed format, but
it trades a pip install for a binary every user and every CI runner must have, and it
puts the passphrase on a subprocess boundary. Worth revisiting if the dependency proves
painful.

## The passphrase

**A file, not a prompt.** The MCP server runs headless under Claude Desktop, and
`docs/mcp-hardening.md` forbids anything that can block it — a server waiting on stdin
hangs forever.

Resolution order: `SECOND_BRAIN_PASSPHRASE` → the file at git config
`secondbrain.passphrasefile` → the default `~/.config/second-brain/<brain>.key`.

The default lives **outside the repo**, mode `0600`. That is the point: a secret inside
the working tree is one `git add -f` or one careless `.gitignore` edit away from the
remote, which is the exact failure this feature exists to prevent. An in-repo path is
permitted, but pre-commit refuses to commit it and `doctor.py` warns.

`secondbrain.passphrasefile` is per-machine and uncommitted — the same pattern
`secondbrain.autosync` already uses.

*Deferred: OS keychain.* Better ergonomics, but macOS-specific and it re-introduces a
prompt the MCP server cannot answer.

### Confirming the passphrase is right

`enc/keyfile.json` is tracked and contains no secret:

```json
{"v":1, "kdf":"scrypt", "n":131072, "r":8, "p":1,
 "salt":"<base64>", "verify":"<HMAC tag>", "hint":"the usual one, plus the year"}
```

Derive the key, compute `HMAC(k_verify, "second-brain-v1")`, compare constant-time
against `verify`. One cheap check answers "is this passphrase correct?" **before** any
note is touched — without it a typo produces N unintelligible AEAD failures instead of
one clear *wrong passphrase*.

The `hint` is optional free text, set with `--set-hint`. Two caveats the README must
carry rather than bury:

- the hint is **readable by anyone who can read the repo**, so a hint good enough to
  remind you may be good enough to narrow a guess. Never make it a function of the
  passphrase itself.
- salt + verifier make **offline brute force** possible by construction. The scrypt cost
  is the entire defense, which is why `n` is `2**17` rather than a comfortable default.

**Losing the passphrase loses the brain — unidentifiably.** With names encrypted you
cannot even enumerate what you lost. Escrow moves from good practice to a documented
prerequisite, alongside the credential preflight `--remote` already performs.

## The four call-sites that go blind

Once `vault/**` is git-ignored, every mechanism that selects work by *what git staged*
stops seeing anything — and none of them fails loudly. This is the "observer goes
blind" shape: the logic is fine, its window no longer contains the subject. Rewiring
these to trigger on the note being encrypted **is** the bulk of the task:

1. `scripts/embed_staged.py:39` filters staged paths ending `.md` → nothing staged →
   **notes silently stop being embedded on commit.** The hook still exits 0.
2. `scripts/mcp_server.py:497` runs `git add -- <note>.md` → git refuses an ignored
   pathspec → `add_note` fails mid-commit, which is the #28 poisoning shape.
3. `.githooks/pre-commit`'s `git diff --cached --name-only -- '*.md'` line-count guard →
   never fires again.
4. `scripts/glossary_autolink_staged.py` → same selector, same silence.

### Commit messages

`mcp_server.py` commits `note: add {title}` (line 498) and `glossary: add {term}`
(line 670). Encrypting the filename while the git log prints the title is theater.

Both switch to the **encrypted name** — `note: add JBSWY3DPEHPK3PXPKRUG` — which keeps
per-note traceability at one level of indirection rather than blanking it.
`--path-of` resolves one; `--decode-log` renders `git log --oneline` in plaintext on a
machine that holds the key.

## Configuration

`config/features.toml`, tracked, because every clone must agree — a peer with the
toggle off commits plaintext into the same remote:

```toml
[encryption]
enabled = true
```

Precedence is the house standard, `env > file > default`
(`SECOND_BRAIN_ENCRYPTION`), and the default is `false`.

**But the toggle is a migration, not a flag.** `enabled = true` in a brain whose notes
are still plaintext is an inconsistent state, not a request. The transition runs through
`scripts/encrypt_vault.py`:

- `--enable` — preflight (passphrase reachable, tree clean, remote-history warning),
  write `keyfile.json`, encrypt every content note, untrack the plaintext, install the
  ignore rules, set the toggle, commit.
- `--decrypt` — hydrate a fresh clone: every blob back to its header's path.
- `--disable` — the reverse, with the same "history still holds the ciphertext" caveat
  the enable path gives about plaintext.

`tools/check_config_matrix.py` (gate 10) fails on any key in `features.toml` without a
MATRIX entry, so this toggle needs one — special-cased, since its "flip" is a migration
rather than a value.

### `.gitignore` when enabled

Default-deny over the vault, so a future file type — an Obsidian `.canvas`, an
attachment, a stray export — cannot silently leak. Same allowlist shape the workspace
wrapper uses for its managed children:

```gitignore
# Every note is content — default-deny.
/vault/**
# The PARA skeleton (universal names, zero information) and the devkit-owned template.
!/vault/*/
!/vault/*/.gitkeep
!/vault/templates/new-note.md
```

Git cannot re-include a file underneath an excluded **directory**, which is why
`!/vault/*/` is there. That subtlety fails *open* — get it wrong and notes leak while
everything looks fine — so it is pinned by a test.

## doctor.py

- passphrase resolvable, and correct (the verifier check)
- every content note has a current `.md.enc`; no orphan blobs
- no plaintext note staged or tracked
- `enabled` agrees with what is on disk (catches a half-finished migration)
- the passphrase file is not inside the repo

## Testing

The golden stays plaintext — the feature is off by default — so the ON path cannot be
prototyped there without destroying the regression baseline. It gets a hermetic gate
that generates a throwaway brain (the `check_config_matrix.py` pattern), enables
encryption, clones it, decrypts, and asserts a byte-identical round-trip.

The load-bearing assertion is a **canary**: a known phrase written into a note, and a
note filename that is itself a canary, must both be absent from a fresh clone's object
store and from `git log -p`. Per the "tests that cannot fail" rule, that one is
**mutation-tested** — break the encryptor on purpose and confirm the gate goes red —
because it is precisely the kind of check that passes forever without ever comparing
anything.

Also pinned: the four blinded call-sites still do their jobs with encryption on
(especially "a commit still embeds the note"), and the `.gitignore` allowlist.

## Build order

1. `scripts/encrypt_vault.py` — envelope, KDF, keyfile, name derivation — plus dev-only
   unit tests in the devkit.
2. Rewire the four call-sites; make each one's coverage fail first with encryption on.
3. `--enable` / `--decrypt` / `--disable`, and the `.gitignore` allowlist.
4. `doctor.py` checks; README section, including the "does not reach back into history"
   warning.
5. The hermetic CI gate + the mutation check; the classification gate.
6. Prototype in the golden with the toggle **off** (proving the no-op path is
   bit-identical), vendor, template, `tools/ci.py`.
