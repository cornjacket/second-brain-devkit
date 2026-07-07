# Remote-backed brains — connect a new brain to a git remote at creation

**Status:** task — to build (the **very next** task). Design below; nothing built yet.

`new_brain.py` today `git init`s a **local-only** repo with no remote (verified). That
leaves a hole: no off-machine **backup**, no **multi-machine** use, and no foundation for
the shared/sync design ([big-brain.md §0 + Approach A](big-brain.md)). This task adds the
*connect-and-push-at-creation* step. Ongoing pull/sync automation (the `post-merge` hook,
conflict handling) is [big-brain Approach A](big-brain.md) and layers on top later.

## Scope

- **In:** at creation, optionally attach a git remote and push the scaffold, following the
  standard git workflow; a preflight that verifies prerequisites; README docs.
- **Out (separate, later):** the ongoing sync loop (pull → re-embed/hydrate, push after
  commits, merge-conflict UX) — that's big-brain Approach A. Attaching a remote to an
  *already-created* brain — a small follow-up (`--remote` on `update_brain.py`, or a
  `tools/connect_remote.py`).

## Design (recommended)

1. **Opt-in, not mandatory — `new_brain.py --remote <URL>`.** Local-only stays the
   default so offline / single-machine / air-gapped creation still works (core
   local-first). With `--remote`, connect + push; without it, today's behavior.

2. **Standard git flow, appended to the current steps.** After `git init` → first commit
   (`--no-verify`) → wire `core.hooksPath`, add:
   - `git remote add origin <URL>`
   - `git push -u origin HEAD`  *(HEAD, not a hard-coded `main`, so it's branch-name-
     agnostic; sets upstream so later `git pull`/`push` need no args)*

3. **Preflight verify — detect + instruct, never auto-configure credentials.** Before the
   push (ideally before generating anything, to fail early), check:
   - **git identity** set (`user.name`/`user.email`) — else the first commit can't be made;
   - **credentials + reachability**: `git ls-remote <URL>` succeeds (this is the single
     best probe — it exercises the exact auth path the push will use, SSH or HTTPS);
   - **remote is empty**: `git ls-remote <URL>` returns no refs — pushing into a non-empty
     remote would reject or entangle histories.
   On any failure: print the **exact fix** and stop before mutating anything. This mirrors
   `doctor.py` / `install_skill.py` (`--apply`-gated, detect + instruct) — the devkit
   never auto-installs or auto-configures a user's environment.

4. **Failure handling is non-destructive.** The remote step runs **after** the local brain
   is fully generated + committed, so if the push fails the user still has a complete,
   usable local brain — print how to `git remote add` + `git push -u origin HEAD` by hand.
   Never leave a half-created dir. (If the preflight runs *before* generation, a creds
   failure means nothing was created at all — cleanest.)

5. **README — a "Back it up / share it (git remote)" prerequisites section.** Document:
   create an **empty** remote repo (GitHub/GitLab/self-hosted); set up credentials **once
   per machine** — SSH (key in `ssh-agent`) *or* HTTPS (a token via a credential helper);
   then `new_brain.py ~/my-brain --remote <URL>`. Note both auth methods and how to verify
   (`git ls-remote <URL>`).

**Why not a credential-creating pre-setup script?** Generating SSH keys / provisioning
tokens is invasive, platform- and provider-specific, and sometimes needs interactive
auth — the same reasons the devkit chose *detect + instruct* over auto-install for Ollama.
A **preflight verify** (does auth already work?) is the right amount of automation; a
credential *installer* is not. If we want a single "am I ready to create a remote-backed
brain?" command, fold the checks into `doctor.py` or a tiny `--check` mode of `new_brain`.

## State — how scripts know a brain is remote-backed

Downstream scripts (the post-commit push, the `post-merge` pull-reaction — big-brain
Approach A) must know whether to touch a remote. Two *distinct* facts, and only one is new:

1. **"Is a remote configured?" — git already persists this.** `git remote get-url origin`
   (and the upstream `git rev-parse --abbrev-ref @{u}`) are the source of truth; no
   invented state file. A `--remote`-created brain has `origin` set by us; a **cloned**
   brain (an Approach-A peer) has it set automatically by `git clone`. Scripts query git.
2. **"Should the hooks auto-sync (pull/push)?" — a new per-machine toggle.** You can have a
   remote yet not want every commit to push (offline, slow link, manual-sync preference).
   Store this as a **local git-config key**, e.g. `git config secondbrain.autosync true`,
   set by `new_brain --remote` on a successful push. It lives in `.git/config` → per-repo,
   **per-machine, not committed** — so each clone/machine chooses its own sync behavior (a
   *committed* flag would wrongly force one policy on all peers). It's also cheap to read
   from shell hooks (`git config --bool --get secondbrain.autosync`).

The sync scripts then gate on **both**: *remote exists* **and** *autosync on* → act
(warn-not-block on failure, matching the existing hooks). This task **defines and sets**
that state at connect time; big-brain Approach A **consumes** it. (Manual override: a user
flips `secondbrain.autosync` to pause/resume auto-sync without removing the remote.)

## Testing — a local bare remote (no creds, CI-friendly)

A git remote need not be a network server: `git init --bare <path>` is a fully-functional
remote addressed by a `file://` path. So the entire flow is testable in the harness/CI
**without any network or credentials** (verified):

- create a bare repo → use it as `--remote file://…/remote.git`;
- assert the preflight probes (`ls-remote` succeeds, remote is empty), then the push lands
  the scaffold in the bare repo;
- `git clone` the bare repo into a second dir = an **Approach-A peer**, and assert it
  receives the notes (and that `origin`/autosync state is correct on both sides).

This exercises the real `remote add` / `push` / `pull` / `ls-remote` code paths; only the
**auth** layer (SSH/HTTPS) is skipped — a per-machine concern the runtime preflight covers,
not something CI should carry secrets for. A `tools/check_remote_sync.py` (opt-in, like the
other behavioral checks) can own this against a temp bare repo.

## Open questions

- **Branch name** — standardize on `main` (`git branch -M main` before push) or stay
  agnostic with `push HEAD`? (Leaning: push `HEAD`, don't rename the user's default.)
- **Create the remote for the user?** No by default (would tie us to `gh`/`glab` + a
  provider). Require a pre-created empty repo. A `--create-remote` via `gh` could be a
  later convenience, gated on the CLI being present.
- **Private by default?** The devkit doesn't create the repo, so this is the user's choice
  at repo-creation time — just call it out in the README (a brain is personal data).
- **Attach-to-existing** — same mechanism for a brain that already exists (see *Out*).

## Relationship to big-brain

This is the **foundation** of [big-brain Approach A](big-brain.md): "connected" (a remote
exists, scaffold pushed) comes first; "synced" (pull → re-embed/hydrate, push-after-write,
conflict handling via a `post-merge` hook) is Approach A on top. Do this first.
