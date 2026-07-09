---
tags: [seed, typescript]
---

# Decorators

Decorators are functions applied with the `@expression` syntax to classes, methods, accessors, properties, and parameters to observe or replace their definition. The legacy form, gated behind the `experimentalDecorators` compiler flag, pairs with `emitDecoratorMetadata` and `reflect-metadata` so frameworks like Angular and NestJS can read design-time type metadata via `Reflect.getMetadata` for dependency injection. The TC39 Stage 3 standard decorators that tsc now emits have a different signature: each receives the decorated value plus a context object exposing `kind`, `name`, `addInitializer`, and `access`, and may return a replacement. A decorator factory is just a function returning the actual decorator, letting you parameterize it — `@Component({...})`, `@Injectable()`, `@Input()`. Property and parameter decorators cannot alter types, only runtime behavior. Evaluation order runs outermost factory first, then applies bottom-up.
