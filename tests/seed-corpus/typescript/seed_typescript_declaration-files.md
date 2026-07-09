---
tags: [seed, typescript]
---

# Declaration files

A .d.ts declaration file carries only type information — ambient declarations, no emitted JavaScript — so typed code can consume libraries authored in plain JavaScript. Inside them you write `declare module`, `declare global`, `declare const`, and ambient namespaces that describe the runtime surface without implementing it. The DefinitelyTyped repository publishes community-maintained declarations under the `@types/*` scope, resolved automatically through the `typeRoots` and `types` compiler options. A library that authors its own types sets `"declaration": true` in tsconfig.json so tsc emits a .d.ts beside each module, then points the `types` (or legacy `typings`) field in package.json at the entrypoint. Triple-slash directives like `/// <reference types="node" />` pull in dependent ambient declarations. Declaration merging lets a .d.ts augment an existing interface or module, which is how you extend third-party shapes without forking them.
