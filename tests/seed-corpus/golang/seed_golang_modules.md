---
tags: [seed, golang]
---

# Modules and packages

A Go module is the unit of versioning and dependency management, rooted at a go.mod file that declares the module path, the go directive naming the language version, and require lines pinning each dependency to a semantic version. A companion go.sum records cryptographic checksums so builds are verifiable and reproducible. Modules replaced the old GOPATH src layout: you now work anywhere, and go get adds or upgrades a dependency while go mod tidy prunes unused requires and fills in missing ones from your imports. A module groups packages, each a directory whose files share a package clause, and identifiers are exported when capitalized. Semantic import versioning appends the major version to the path, as in example.com/lib/v2, so v2 and later coexist. The go.mod replace and exclude directives redirect or forbid versions, and the module proxy at proxy.golang.org plus GOPROXY cache the graph. Minimal version selection resolves the build list.
