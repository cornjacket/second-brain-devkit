# Claude Desktop e2e — human-driven, script-verified (task #33)

The one test the automated harness cannot run. `tools/check_mcp_server.py` (CI gate G6) drives
the stdio server with a **Python** MCP client — so it is blind to bugs that only appear in the
**real Claude Desktop client** (the `outputSchema` drop, `docs/mcp-server.md` §11). There is no
API to drive Desktop's GUI, so **a human is the driver**: paste the canned prompts below, then run
the verifiers. The verifiers assert **deterministic side effects** (a note created + committed, a
glossary term defined) — never the model's prose. A few checks are inherently human-observed
(a refused read, search ranking); those print as `MANUAL`.

This is **release acceptance, not a CI gate** — run it after a Desktop update or an MCP-surface
change. Same class as the Obsidian hand-tests in `PLAN.md`.

## Primary path — against your real brain, on a disposable branch (task #34)

Your Claude Desktop is already pointed at your **real** brain (`~/second-brain`). Re-pointing it at
a fresh fixture every run means editing `claude_desktop_config.json` + restarting Desktop — enough
friction that the suite never runs. So instead isolate the whole run on a throwaway git branch:
Desktop's MCP server operates on whatever is checked out, so **a disposable branch *is* the
throwaway brain**. Every note the scenarios write commits onto that branch; teardown deletes it and
rebuilds the search index so your base branch comes back **byte-identical** — with **zero Desktop
reconfiguration**. Design + correctness notes: `../docs/desktop-e2e-disposable-branch.md`.

```
desktop-e2e/setup.sh                       # assert clean + doctor green, then git checkout -b e2e-run
#   … paste the prompts below into Desktop, in order …
python3 desktop-e2e/verify/run_all.py --brain ~/second-brain
desktop-e2e/teardown.sh                    # delete the branch, rebuild the index, assert byte-identical
```

`setup.sh`/`teardown.sh` default to `~/second-brain` and branch `e2e-run` (override with `--brain`
/ `--branch`). **Requires a clean base branch** — uncommitted work would be carried onto the
branch, so setup refuses to start until the tree is clean. Teardown fails **loudly** (non-zero) if
HEAD moved, the tree is dirty, or the index is not green after restore — that assertion doubles as
a standalone "did it clean up?" check. This exercises **your live Desktop setup + current code**;
to instead certify **what the generator emits to a brand-new user**, use the fresh-fixture path
below.

## Alternative path — a fresh fixture brain (certifies generator output)

1. **Generate a fresh fixture brain** (never run the scenarios against your real brain directly —
   they write notes; the disposable-branch path above is what makes the real brain safe):
   ```
   python3 tools/create_second_brain.py /tmp/e2e-brain
   cd /tmp/e2e-brain && pip install -r requirements.txt && pip install -r requirements-mcp.txt
   git config core.hooksPath .githooks        # so add_note embeds + commits
   ```
2. **Point Claude Desktop at it.** In `claude_desktop_config.json` add a server whose command is
   `python3 /tmp/e2e-brain/scripts/mcp_server.py`, then restart Desktop. Confirm the connector
   shows its tools (if it shows "no tools available", suspect §11).

## Run

Do the scenarios **in order** (02 depends on 01 seeding the vocabulary). For each: paste the
prompt from `prompts/NN-*.md` into Desktop, eyeball the expected reply, then run its verifier.
Or run them all at once after doing all the pastes (point `--brain` at whichever brain you set up —
`~/second-brain` for the disposable-branch path, `/tmp/e2e-brain` for the fixture path):

```
python3 desktop-e2e/verify/run_all.py --brain ~/second-brain
```

`PASS`/`FAIL` are deterministic (brain state); `MANUAL` items you confirm by eye in Desktop.
Exit 0 means every deterministic check held — it does **not** mean the MANUAL items passed.

## Scenarios

| # | Prompt | Deterministic check | Human-observed |
|---|---|---|---|
| 01 | add a note (`ai-agents`, `planning`) | note exists, tags right, committed | reply says "created …" |
| 02 | add a note with a **near-miss** tag `ai-agent` | note exists; brain's rule maps `ai-agent`→`ai-agents` | reply carries a `TAG HINT:` line (task #32) |
| 03 | add a glossary term `ablation study` | glossary note exists, def + alias, committed | reply says "defined …" |
| 04 | `get_note` on `/etc/passwd` | — | reply **refused**, no file contents |
| 05 | search "how do vector databases work" | — | right seed notes surface |

Scenario 02 is the point of the whole suite: it proves the write-time near-miss warning
**reaches the model inside Desktop**, which the Python-client harness can never show.
