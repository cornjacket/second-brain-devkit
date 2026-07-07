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
