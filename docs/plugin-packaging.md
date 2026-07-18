# Plugin packaging — one Claude Code plugin vs. the skill + MCP two-step (task #23)

**Verdict up front: a single Claude Code plugin cannot collapse the current two-step, because
the two steps serve two different surfaces and a plugin reaches only one of them.** The plugin
can tidy the *CLI* half (which is already a one-liner) but does nothing for the half that
actually hurts — registering the MCP server for Claude **Desktop's Chat tab**, which is where a
brain is used. This is a research note (notes only); no code changes proposed here.

## The two-step today, and which surface each serves

A brain ships two independent access paths because two client families reach tools two different
ways:

1. **Skill install** — `python3 scripts/install_skill.py --global --nudge --apply` symlinks
   `skill/second-brain/` (`query.py` + `SKILL.md`) into `~/.claude/skills/` and `~/.gemini/skills/`.
   Serves **any client that can run a shell command**: Claude Code, Gemini CLI. Cost is near zero
   and it is already a single command. See the brain README "Query it from any project".
2. **MCP registration** — hand-edit `claude_desktop_config.json` to add the `second-brain` MCP
   server (absolute interpreter path + `scripts/mcp_server.py`). Serves **Claude Desktop**, which
   *cannot* shell out and so reaches tools only over MCP. This is the "gotcha" step
   ([claude-desktop-workflow.md](claude-desktop-workflow.md) §5) — the #1 "server won't start"
   support cause (wrong interpreter path) and the only genuinely fiddly part of onboarding.

So the pain is concentrated in step 2, and step 2 is a **Desktop** problem.

## What a Claude Code plugin is (confirmed against current docs, 2026-07)

A Claude Code plugin is a self-contained directory (`.claude-plugin/plugin.json` manifest, plus
`skills/`, `agents/`, `hooks/`, `.mcp.json`, etc. at the plugin root) that bundles skills, an MCP
server, slash commands, hooks, and subagents **together**. Installing it (`/plugin install
name@marketplace`, distributed from a GitHub repo with a `marketplace.json`) auto-registers the
bundled MCP server — no separate `claude mcp add`. Dependencies (Python, the `mcp` SDK, Ollama)
are **not** bundled; the user still installs those, and a plugin cannot run a setup step.

Sources: code.claude.com/docs `plugins`, `plugins-reference`, `mcp`, `desktop`.

## The crux: a plugin's MCP server does not reach where the brain is used on Desktop

A plugin's bundled MCP server becomes available in **Claude Code CLI** and **Claude Desktop's Code
tab** (local/SSH sessions) — and **only** there. It is **not** available in Desktop's **Chat** or
**Cowork** tabs, and it does **not** get written into `claude_desktop_config.json` (that registry
is separate and feeds all Desktop tabs).

The brain's Desktop experience is explicitly the plain **Chat** tab —
[claude-desktop-workflow.md](claude-desktop-workflow.md) §8: *"In a plain Chat (not Cowork/Code),
point at the tool."* That is the whole value proposition: casually chatting with your notes, not
an agentic coding session. **A Claude Code plugin's MCP server never appears in that tab**, so the
plugin cannot replace step 2.

## Verdict per surface

- **CLI / skill side (Claude Code, Gemini):** a plugin *could* bundle the skill (and, for the Code
  tab, the MCP server) and give a nicer marketplace install. But this side is already one command,
  and a plugin is **Claude-only** — moving the skill into a plugin would **drop Gemini CLI support**
  (plugins are not a Gemini concept), or force us to keep the standalone skill install anyway. Net
  gain: marginal, with a real regression risk. Not worth it on its own.
- **Desktop / MCP side (the painful step):** a Claude Code plugin **does not help at all** — wrong
  surface. The MCP server would have to be reached from Desktop's Code tab, which is not how a brain
  is meant to be used on Desktop.

## The path that would actually simplify the Desktop step

If we want to kill the manual `claude_desktop_config.json` edit, the mechanism is a **Desktop-native
one** — Desktop **Connectors** (the GUI-driven MCP setup flow the docs mention) and/or an **MCP
bundle** (`.mcpb`, formerly `.dxt` "Desktop Extension") — a one-click install of a local MCP server
into Desktop that feeds the Chat tab. This is a **separate packaging system from Claude Code
plugins** and is the correct thing to research if reducing Desktop onboarding friction is the goal.

> ⚠️ Unverified here: the exact current state of `.mcpb`/Desktop Extensions (naming, whether it can
> point at an existing interpreter + `mcp_server.py`, whether it handles the absolute-path gotcha for
> us). The guide research above focused on plugins; treat the `.mcpb` route as the **open follow-up**,
> not a settled fact. There is no prior decision on any of this in the second brain — this is new
> ground.

## Recommendation

- **Do not** repackage the brain as a Claude Code plugin to unify onboarding — it cannot, because
  the hard step lives on a surface (Desktop Chat) that plugins do not serve, and it would risk the
  Gemini skill path.
- **A plugin is still worth a small, separate look** for one narrow win: distributing the **skill**
  (plus hooks/agents) to Claude Code users via a marketplace `/plugin install` instead of the
  `install_skill.py` symlink — purely a nicer CLI install, not a consolidation of the two-step. Low
  priority; the current script already works and covers Gemini too.
- **The real Desktop-onboarding win is `.mcpb`/Connectors**, tracked as a follow-up. That is where
  the "one-click, no config edit" outcome actually lives.

## Open follow-ups

- Verify the current `.mcpb` / Desktop Extension format and whether it can wrap this brain's stdio
  MCP server (interpreter + `mcp_server.py`) into a one-click Desktop install, and whether it solves
  the absolute-interpreter-path gotcha.
- Decide whether a Claude-Code-marketplace skill distribution is worth adding **alongside** (not
  replacing) `install_skill.py`, given it drops Gemini.
