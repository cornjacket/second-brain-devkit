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
- the devkit's own docs and the single path `vault/templates/new-note.md` — identical in
  every brain, so they say nothing about you. **No other directory under `vault/` is
  committed at all** (see "Subdirectories" below)
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

### Subdirectories

You are free to organise `vault/projects/` into whatever tree you like — the HMAC is
taken over the **full relative path**, so depth is irrelevant and
`vault/projects/2026/kitchen-remodel/notes.md` encrypts exactly like a top-level note.

**No directory under `vault/` is committed when encryption is on.** Git tracks files,
not directories, so once `vault/**` is ignored, a subdirectory's *name* never reaches a
tree object — which is the point: a folder called `divorce/` is a tell even when every
note inside it is unreadable. The structure exists only in the working tree and in the
encrypted headers.

The tree is therefore **reconstructed, not restored**:

- `--decrypt` reads each header's `path` and `mkdir -p`s its parent before writing.
  Arbitrary depth, in one pass, with no directory metadata committed anywhere.
- The **PARA skeleton** (`projects/`, `areas/`, `resources/`, `archive/`, `glossary/`,
  `templates/`) is recreated from the devkit's own constant — the same list
  `seed_vault.py` uses — not from committed `.gitkeep` files.

That last point is a leak, not a convenience. Today the golden commits `.gitkeep` only
in the buckets that happen to be *empty* (`archive/`, `glossary/`), so under encryption
the **presence or absence of a `.gitkeep` would advertise which buckets you use**. The
ignore rules therefore commit none of them, and the skeleton comes from a constant that
is identical in every brain.

**Documented gap:** an *empty* subdirectory is not preserved. Git cannot represent one
without a placeholder file, and a placeholder is precisely the tell above. A folder you
created but have not written a note into yet will not survive a clone.

**Moving a note between subdirectories changes its path, hence its opaque name**, so git
sees a delete plus an add rather than a rename. That is the same cost noted above for
renames, and it is what keeps the name from leaking where a note lives.

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
# Every note is content — default-deny. No directory under vault/ is committed:
# a folder name is a tell even when the notes inside it are unreadable.
/vault/**
# Exactly one exception — the devkit-owned note template (gate 9 needs it readable).
!/vault/templates/
!/vault/templates/new-note.md
```

Two subtleties, both of which fail **open** — get either wrong and notes leak while
everything looks fine — so both are pinned by a test:

- Git cannot re-include a file underneath an excluded **directory**, which is why
  `!/vault/templates/` must precede the file negation. It is scoped to that one
  directory rather than `!/vault/*/`, so no other bucket is even mentioned.
- **No `.gitkeep` is re-included.** The skeleton is recreated from the devkit constant
  instead; committing placeholders would advertise which buckets are empty.

## doctor.py

- passphrase resolvable, and correct (the verifier check)
- every content note has a current `.md.enc`; no orphan blobs
- no plaintext note staged or tracked
- `enabled` agrees with what is on disk (catches a half-finished migration)
- the passphrase file is not inside the repo
- **nothing under `vault/` is tracked except `templates/new-note.md`** — a positive
  assertion over `git ls-files vault/`, so a stray `git add -f` or a hand-edited ignore
  rule is caught rather than assumed away

## Testing

The golden stays plaintext — the feature is off by default — so the ON path cannot be
prototyped there without destroying the regression baseline. It gets a hermetic gate
that generates a throwaway brain (the `check_config_matrix.py` pattern), enables
encryption, clones it, decrypts, and asserts a byte-identical round-trip.

### What the OFF case is covered by today, and what it is missing

**A plaintext brain commits its notes under `vault/`, and that is deliberate.** The
`.gitignore` ignores only derived or foreign things there — `.*.embed.json` sidecars,
`*.pdf`, `.obsidian/` — so every `.md` is tracked. Empirically true in the real brain:
48 tracked notes under `vault/`.

It is *asserted* in exactly one place: `tests/test_pdf_gitignore.py:50`,
`test_notes_are_still_committed`, which checks `vault/resources/some-note.md` is not
ignored. That exists as an over-reach guard on the PDF rule, not as coverage of this
property, and it has two blind spots this task must close **before** touching the ignore
rules — otherwise the OFF-case regression net is one assertion wide:

- it checks a single PARA root; the PDF test next to it loops over all four
- it asks `git check-ignore`, which answers "would this be ignored", not "is the brain's
  content actually tracked"

**OFF-case cases** (must hold whether or not this feature ever ships — these run in the
golden, so they are the regression net that proves encryption changed nothing):

| # | Case | Assertion |
| --- | --- | --- |
| 1 | a note in **every** PARA root, plus `glossary/`, is not ignored | `git check-ignore` says no, for each root |
| 2 | a note in a **subdirectory** at two depths is not ignored | same, for `projects/a/b/note.md` |
| 3 | notes are **actually tracked**, not merely un-ignored | `git ls-files 'vault/**/*.md'` is non-empty and contains the seeded notes |
| 4 | no `enc/` directory exists and no `.md.enc` is tracked | the encrypted layout is absent when the toggle is off |
| 5 | the generated brain is **bit-identical** to today's with the toggle off | existing G2 structural diff, unchanged |

### ON-case cases

Hermetic: generate a throwaway brain, enable encryption, add notes, clone, decrypt.

| # | Case | Assertion |
| --- | --- | --- |
| 6 | **round-trip** | decrypt of a fresh clone reproduces every note **byte-identically** |
| 7 | **body canary** | a known phrase in a note appears nowhere in the clone's object store or `git log -p` |
| 8 | **filename canary** | a note named for a canary word — the word appears in no tracked path, no `git log --stat`, no tree object |
| 9 | **no plaintext tracked** | `git ls-files vault/` returns exactly `vault/templates/new-note.md` |
| 10 | **subdirectory round-trip** | notes at two depths under two buckets restore to the identical tree |
| 11 | **empty bucket leaves no trace** | a bucket with no notes is invisible in `ls-files`/`log --stat` — what a committed `.gitkeep` would have given away |
| 12 | **no churn** | re-running the encryptor with no edits produces **zero** diff (the `phash` skip-gate) |
| 13 | **stable name** | editing a note's body leaves its opaque name unchanged |
| 14 | **orphan sweep** | deleting a note removes its blob; renaming produces delete + add, no leftover |
| 15 | **wrong passphrase** | fails once with a clear message from the verifier, before any note is touched |
| 16 | **commit messages** | no title or term appears in `git log`; the opaque name does |
| 17 | **the four blinded call-sites** | a commit still embeds the note; `add_note` still commits; the line-count guard still warns; glossary autolink still runs |
| 18 | **classification** | every emitted `.md` lands in exactly one bucket; an unclassified new file fails the gate |
| 19 | **passphrase file not committable** | an in-repo passphrase path is refused by pre-commit and reported by `doctor` |
| 20 | **migration is resumable** | an interrupted `--enable` leaves a state `doctor` names, never a half-encrypted brain reported as healthy |

### The one that gets mutation-tested

Cases 7 and 8 are **absence** assertions — the exact shape that passes forever without
ever comparing anything, per the "tests that cannot fail" rule. Both get broken on
purpose (encryptor stubbed to pass the plaintext through) and confirmed red before they
are trusted. Case 3 gets the same treatment for the opposite reason: it is the assertion
standing between "we ignore the right things" and "we silently stopped committing the
user's notes."

## Manual verification: a parallel encrypted twin

The hermetic gate proves the mechanism on throwaway fixtures. It cannot answer the
question the owner of a brain actually wants answered — *"is my real content absent from
my real git history?"* — because a fixture brain contains nothing the user would
recognise. So the feature also gets a **human-driven twin**, the same shape as the
desktop-e2e suites (#33/#34/#35): not a CI gate, a thing a person looks at.

```
~/second-brain/            the real brain — plaintext, untouched, never modified by this
~/second-brain-encrypt/    the twin — same notes, encryption ON
```

The twin is a **note-for-note copy** of the real brain with the toggle enabled, so every
note has a plaintext original to compare against. Comparison is then a two-layer check:
you read the twin's `git log`/`ls-files` yourself and recognise nothing, **and** a
verifier asserts the same mechanically — because "I looked and it seemed fine" is
exactly the check that passes forever without comparing anything.

### The mirror script

**One-way by default: real → twin.** The real brain is the source of truth and is never
written to. A `--reverse` exists for testing the Desktop write path (a note added into
the twin flowing back), but it is explicit, refuses to overwrite an existing note, and is
not part of the normal loop. Bidirectional-by-default would put test junk in the one
brain that matters.

Modes:

- `--mirror` — copy every note from the real vault into the twin's, then encrypt and
  commit. Idempotent; a second run with no upstream edits produces no commit.
- `--verify` — the mechanical half of the comparison:
  1. every real note exists in the twin, and **decrypts byte-identically**
  2. `git ls-files` in the twin returns nothing under `vault/` but the note template
  3. every real note's **filename stem** appears in no tracked path and in no commit
     message in the twin
  4. a sample of real note **content lines** appears nowhere in the twin's object store
     (`git log -p`, `git cat-file --batch` over all blobs)
  5. the two brains' note **counts** agree
- `--teardown` — remove the twin. It holds real personal content in its working tree;
  it should not linger once a run is done.

**Where it lives.** The ask was for a script that lives only in the twin, so nothing new
lands in the real brain — that constraint is preserved either way, and the
recommendation is that the **devkit owns it** at `tools/mirror_brain.py`, invoked against
the twin. A script living inside a *generated* brain is un-versioned by the devkit, lost
on any regenerate, reported as an unknown file by `update_brain.py`, and would need an
`emit-manifest.toml` entry to keep the partition invariant clean. Devkit-owned, never
emitted, is the same call `tools/vendor_golden.py` and the ablation tooling already make.

### Scope: a copy target, not a second brain

**No MCP server and no skill for the twin.** It is not a brain anybody uses — it is a
*copy target*, and its whole job is to hold the same notes so their committed form can be
inspected. Adding a second server and a second skill would buy a second way to write
notes nobody reads, at the cost of both collisions below.

So the loop is: copy `.md` files from `~/second-brain/vault/` into the twin, encrypt,
commit, push, look at what the remote holds. `~/second-brain-encrypt` already exists as
an empty clone of `git@github.com:cornjacket/second-brain-encrypt.git`.

The collisions below are kept as the *reason* the twin stays a copy target, and as the
warning if it ever grows one.

### If the twin ever does get a server — two collisions

The twin needs its own MCP server entry so it can be exercised through the same interface
the real brain uses. Two things collide on the name `second-brain`:

1. **There is one skill slot per machine.** `install_skill.py` always symlinks the same
   fixed path, `~/.claude/skills/second-brain` → `<BRAIN>/skill/second-brain`, whichever
   brain it is run from — and the skill resolves its brain from where that link lands. So
   running it from the twin repoints every project's `/second-brain` query at the test
   brain. Purely an artifact of running two brains on one machine; with one brain it never
   arises. **Workaround: don't run it from the twin** — the twin is exercised through
   Desktop's MCP server and `git`, and CLI search on it works directly
   (`python3 ~/second-brain-encrypt/scripts/search_vault.py "…"`), no skill needed.
   `ls -l ~/.claude/skills/second-brain` shows where the slot points; re-running
   `install_skill.py` from the real brain restores it. `--verify` checks it as a courtesy.
2. **Both servers expose identically-named tools.** Desktop namespaces by server key, so
   both entries coexist, but the model sees two `add_note`s and two
   `search_second_brain`s and can pick the wrong one. The server key is therefore
   `second-brain-encrypt`, distinct at a glance, and write tests name the target
   explicitly. Registering the twin **only for the duration of a run** is the safer habit
   and what the runbook says.

### The remote is a disposable scratchpad

The twin **does** get a remote from the start, and it is the point: a leak that only ever
existed in a local `.git` is not the failure mode this feature guards against. Pushing is
how the twin tests the thing that actually matters — what a *server* ends up holding.

The risk is accepted deliberately and bounded by disposability: a **private** repo,
created for this, deleted the moment a run is done, and never the twin's only copy of
anything. If a run reveals plaintext on the remote, the response is to delete the repo and
fix the encryptor — the twin is a scratchpad, not an archive.

Verification still runs **locally first** (`ls-files`, `git log -p`, `cat-file` over every
blob), because catching a leak before it is pushed is strictly cheaper than after. The
remote is the second look, not the first.

### Sequencing

This subtask runs **after** build steps 1–5, once `--enable` and the hermetic gate exist.
It is the real-brain counterpart to the fixture gate, in the same relationship #34 has to
#33: the mechanism is proven first, then pointed at content the human recognises.

## Build order

At a glance:

| | Step | What it entails |
| --- | --- | --- |
| ✅ | 1. The mechanism | Keys, opaque filenames and the envelope, as pure byte operations that know nothing about git. |
| ✅ | 2. Un-blind the commit path | One shared selector replaces every `git diff --cached -- '*.md'`, so nothing silently stops working when the vault is ignored. |
| ✅ | 3. The migration | `--enable` / `--decrypt` / `--disable` / `--sync` and the default-deny ignore block — the commands a user actually runs. |
| ✅ | 4. Directory reconstruction | Rebuild the note tree from the path inside each envelope, so no folder name is ever committed. |
| ✅ | 5. Make it usable | `doctor.py` preflights, the README section, and promoting the modules + toggle into every generated brain. |
| ✅ | 6. Full acceptance suite | The remaining numbered cases — especially the plaintext net that catches "encryption silently stopped committing notes". |
| ☐ | 7. The parallel twin | A note-for-note encrypted copy of the real brain, so a human can look at what the remote actually holds. |
| ☐ | 8. Ship it | Final vendor → template → `tools/ci.py` pass with the toggle off, proving the no-op path is bit-identical. |

1. **✅ The mechanism** — keys, opaque filenames and the envelope, as pure byte operations
   that know nothing about git.

   `scripts/encrypt_vault.py`: envelope, KDF, keyfile, name derivation, plus
   36 dev-only unit tests. Not emitted yet (classified `exclude`): it has no callers
   until step 2 and no way to be switched on until step 3, so emitting it now would ship
   a brain a module it cannot use. Promote to `verbatim` at step 5, with the toggle.

   Two things worth carrying forward. **The orphan sweep decrypts nothing** — the name is
   a pure function of the path, so every live note's blob name can simply be computed and
   the leftovers *are* the orphans; the earlier plan to decrypt headers for this was
   unnecessary. And **`hashlib.scrypt` needs `maxmem` raised explicitly**: at the shipped
   cost (`n=2**17`, ~134 MB) OpenSSL's built-in 32 MB cap makes it *refuse to run* rather
   than run slowly — a failure only the people using the defaults would ever hit. Both are
   pinned by tests. Measured cost: 0.29 s per derivation.
2. **✅ Un-blind the commit path** — one shared selector replaces every
   `git diff --cached -- '*.md'`, so nothing silently stops working when the vault is
   ignored.

   All four call-sites now go through `scripts/note_selection.py`.
   Plus `scripts/passphrase.py` (file, never a prompt), the working-tree layer on the
   encryptor (`encrypt_file` / `needs_encrypting`), and **CI gate 17**. 15 tests across
   both modes; mutation-tested by restoring the old selector, which turns **5 of the 7**
   encrypted-mode cases red.

   Three decisions worth carrying forward:

   - **A missing passphrase raises.** Returning an empty list would be indistinguishable
     from "nothing changed" — the exact bug the module exists to prevent, reintroduced by
     the code written to fix it.
   - **`add_note` stages the blob and titles the commit with the opaque name.** A log
     printing the note title would undo encrypting the filename.
   - **The `encryption` toggle is deliberately NOT in `features.toml` yet.** Shipping it
     before `--enable` exists would put a switch in a user's config whose documented
     migration does not exist. `features.py` carries the accessor (a missing key reads as
     `false`), and the toggle joins `features.toml` at step 5 — which is also when gate
     10's coverage rule starts applying to it.
3. **✅ The migration** — the commands a user actually runs, plus the ignore rules that
   make them bite.

   `--enable` / `--decrypt` / `--disable` / `--sync`, plus `--name-of`,
   `--path-of` and `--set-hint`, and the `.gitignore` allowlist spliced as a marked block.
   20 end-to-end tests against real throwaway git repos; the three canaries are
   mutation-tested with a pass-through encryptor and all go red.

   **The tests found the limit rather than trusting the doc.** The canaries were first
   written against the whole object store and *failed* — because the seeded plaintext is
   still reachable from the pre-migration commit. That is exactly the documented behaviour,
   so the assertion was corrected to what the feature actually promises (what a commit
   *contains*: `git ls-tree` plus every tracked blob), **and a new test now pins the limit
   itself** — pre-migration history still holds the plaintext, and will fail loudly if
   anyone ever quietly "fixes" it. Consequence, stated plainly: **a brain that has ever
   committed plaintext cannot be made retroactively private by switching this on.** For the
   twin, start from a history that never held plaintext.
4. **✅ Directory reconstruction** — rebuild the note tree from the path inside each
   envelope, so no folder name is ever committed. *(Landed with step 3.)*

   `--decrypt` `mkdir -p`s each header's parent at arbitrary depth, and the PARA skeleton
   comes from `CONTENT_ROOTS` rather than from committed `.gitkeep` placeholders.
5. **✅ Make it usable** — the preflights, the documentation, and actually shipping the
   feature into a generated brain.

   `doctor.py` gained five checks; the README gained an "Encrypt your notes (optional)"
   section carrying the does-not-reach-backwards warning; `encrypt_vault.py`,
   `requirements-crypt.txt` and the `encryption` key moved into the emitted set, and gate
   10 now enforces coverage on the toggle (its fixture runs the real `--enable`, since a
   flip alone would exercise a state no user can reach).

   **Two bugs, both found by running the migration rather than by a test:**

   - **The README claim was false when written.** "Committing a note encrypts it" — nothing
     in the hook chain did that. The pre-commit hook gained a fourth step
     (`encrypt_vault.py --precommit`), last in the chain so the blob carries the text
     glossary auto-linking may have just edited, and a silent no-op — not even a passphrase
     lookup — when the toggle is off.
   - **Enabling encryption destroyed every embedding in the brain.** `git diff-tree` reports
     untracking and deleting identically as `D`, and `update_cache`'s delete path unlinks
     sidecars — so the one commit that untracks the whole vault read as "every note
     deleted" and wiped the lot. Nothing failed, nothing printed. **The working tree is now
     the authority on whether a note exists**, which also fixes the plaintext case of
     untracking a note by hand. Both halves are pinned: untracking is not a deletion, and a
     real deletion still is one.

   `--enable` also now untracks by asking git what it tracks, rather than trusting the note
   list — which is what caught the `.gitkeep` placeholders that would have advertised
   exactly which PARA buckets are empty.
6. **✅ Full acceptance suite** — every numbered case above is covered, and the one that
   is not is named rather than left implied.

   **Cases 1–4** landed first, as `tests/test_notes_are_committed.py`: every PARA root plus
   the glossary, two subdirectory depths, and `git ls-files` rather than only
   `check-ignore` — because a rule can leave a note un-ignored and still have it never reach
   a commit. Hermetic, built from the brain's own shipped `.gitignore`, and
   **mutation-tested**: a vault-swallowing ignore rule turns 14 assertions red. Case 5 is the
   existing G2 structural diff.

   **Case 18** became **CI gate 18** (`tools/check_content_classification.py`): it generates
   a brain, asks `update_brain` about every `.md`, and compares that verdict against what
   `encrypt_vault` actually encrypts. **It found a real hole immediately** — `content_notes`
   enumerated the PARA roots, but the rule says the whole vault, so a note in `vault/inbox/`
   (or any folder invented later) was preserved by every upgrade and silently never backed
   up. Fixed; the gate now discriminates on a `config/*.md` instead.

   **Case 19** needed building, not just testing: `--precommit` now refuses to commit when
   the passphrase file is **staged or tracked** inside the brain. Deliberately narrow — a key
   merely sitting in the repo is untracked and ignored, a bad habit that `doctor` reports
   without stopping work. Committing the key beside the ciphertext it unlocks is not a
   partial leak; it is the whole brain.

   **Honest gap.** Case 16's `add_note` subject line and case 17's fourth call-site — the MCP
   write path under encryption — have no automated test: the server's brain root is a module
   constant, so pointing it at a fixture is not cheap. The code is written and reviewed, and
   the path is exercised by hand in the Desktop suite. Recorded here rather than counted as
   covered.
7. **☐ The parallel twin** — a note-for-note encrypted copy of the real brain, so a human
   can look at what the remote actually holds.

   `tools/mirror_brain.py` + runbook — human-driven, not a CI gate. Note the constraint
   step 3 turned up: the twin must be **encrypted before any note is mirrored in**, or its
   history holds plaintext permanently.
8. **☐ Ship it** — the final pass that proves a brain which never turns encryption on is
   unchanged.

   Golden with the toggle **off** (the no-op path bit-identical), vendor, template,
   `tools/ci.py` green.

### Blocker found at step 1 — since fixed under #41

`vendor_golden.py` and `build_template.py` could not be run when step 1 landed, for reasons
that predate and are independent of encryption. **Resolved 2026-08-13 under task #41**; the
account below is kept because it is why step 1 vendored by hand. The live golden has since been un-bootstrapped from the
old tracker (`be7239a`, `d3e9f11`) and had its `CLAUDE.md` wrapped in managed-block
markers (`f403db2`). So:

- `vendor_golden.py` refuses — the refreshed snapshot no longer partitions the manifest
  (`.claude/hooks/check-daily-plan.py` and `.claude/settings.json` are gone from the live
  golden but still classified in `emit-manifest.toml`);
- `build_template.py` then fails on `CLAUDE.md` — its cleaning transform anchors on the
  old tracker's managed block, which no longer exists, and it wipes `template/` before
  discovering that.

This is **task #41's scenario arriving early**, one step short of the leak it predicted:
the vendor loop broke *loudly* instead of quietly carrying the new tracker's block into
`tests/golden/`, which is the good version of that failure.

Step 1 therefore vendored its three new files **by hand** — they are new, so no drift
could ride along — and CI is green at 16/16. The next step that needs a real
`vendor_golden.py` run must fix the manifest and the `CLAUDE.md` transform first. Doing it
under #41 rather than #42 keeps the encryption work from absorbing a tracker migration.
