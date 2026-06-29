# System Specification & Feature Roadmap

## 0. Open Items

Unresolved design decisions are tracked in [open-questions.md](open-questions.md).
Resolve the relevant item before finalizing any feature it affects.

- **OQ-1:** How should the golden reference repo be stored inside the devkit?
  (version-control vs. live pre-commit hook conflict) — see
  [open-questions.md](open-questions.md#oq-1-how-should-the-golden-reference-repo-be-stored-inside-the-devkit).

## 1. System Architecture Diagram Overview
- Source Note ──> Staged ──> Pre-Commit Hook ──> Update Local `*.embed.json` Array
- Suffix Vector Arrays ──> Bulk Scan ──> Hydrate SQLite `vec0` Virtual Table Cache
- Claude/Gemini Terminal Input ──> Python CLI Matcher ──> Accelerated SIMD Cosine Distance Response

> **Target AI CLIs:** Both Claude (Claude Code) and Gemini (Gemini CLI) are supported terminal frontends. They share the same project memory file; `GEMINI.md` is a symlink to `CLAUDE.md` so both CLIs read identical instructions.

## 2. Storage Specifications
### Sidecar Schema (`*.embed.json`)
```json
{
  "source_file": "path/to/note.md",
  "vector": [0.0, 0.0, "... 768 floating point numbers"]
}
```
