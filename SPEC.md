# System Specification & Feature Roadmap

## 1. System Architecture Diagram Overview
- Source Note ──> Staged ──> Pre-Commit Hook ──> Update Local `*.embed.json` Array
- Suffix Vector Arrays ──> Bulk Scan ──> Hydrate SQLite `vec0` Virtual Table Cache
- Claude Terminal Input ──> Python CLI Matcher ──> Accelerated SIMD Cosine Distance Response

## 2. Storage Specifications
### Sidecar Schema (`*.embed.json`)
```json
{
  "source_file": "path/to/note.md",
  "vector": [0.0, 0.0, "... 768 floating point numbers"]
}
