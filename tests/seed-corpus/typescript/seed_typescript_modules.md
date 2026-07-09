---
tags: [seed, typescript]
---

# Modules

ES modules expose bindings with `export` — named, default, and re-exported via `export * from` — and pull them in with `import`, all statically analyzable at the top level. The compiler resolves specifiers according to the `moduleResolution` strategy (`node16`, `nodenext`, or `bundler`) and the `module` target (`esnext`, `commonjs`), consulting `paths`, `baseUrl`, and the `exports`/`imports` conditions in package.json. Type-only imports written `import type { Foo }` and inline `import { type Bar }` are elided from emit, which `isolatedModules` and `verbatimModuleSyntax` enforce so single-file transpilers never mistake a type for a runtime binding. Dynamic `import()` returns a Promise for code-splitting. Because the import graph is static, bundlers perform tree-shaking to drop unreferenced exports. `esModuleInterop` and `allowSyntheticDefaultImports` reconcile default imports against CommonJS `module.exports`.
