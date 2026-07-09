---
tags: [seed, typescript]
---

# tsconfig and strict mode

tsconfig.json drives the tsc compiler through its `compilerOptions`, plus `include`, `exclude`, `files`, and `extends` for sharing a base config. Turning on `strict` enables the whole family at once: `strictNullChecks`, `noImplicitAny`, `strictFunctionTypes`, `strictBindCallApply`, `strictPropertyInitialization`, `useUnknownInCatchVariables`, and `alwaysStrict`. Complementary linting flags like `noUnusedLocals`, `noUncheckedIndexedAccess`, and `exactOptionalPropertyTypes` tighten it further. `target` sets the ECMAScript output level and `lib` the ambient type libraries, while `module` and `moduleResolution` govern import emit. `outDir`, `rootDir`, `declaration`, and `sourceMap` shape what lands on disk, and `noEmit` defers emit to a bundler. Large repositories set `incremental` with a `.tsbuildinfo` cache and split into composite projects wired together with `references`, built as a graph via `tsc --build`.
