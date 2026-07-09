---
tags: [seed, rust]
---

# Cargo and crates

Cargo is Rust's build tool and package manager. The `Cargo.toml` manifest declares the package name, edition, and `[dependencies]` pulled from crates.io, while `Cargo.lock` pins the exact resolved semver versions for reproducible builds. Everyday subcommands include `cargo build`, `cargo run`, `cargo test`, `cargo check` for a fast type-only pass, and `cargo clippy` for lints. Feature flags in `[features]` gate optional compilation, and `[dev-dependencies]` are compiled only for tests and benchmarks. A crate is the unit of compilation, either a library (`lib.rs`) or binary (`main.rs`), and modules organize items within it. A `[workspace]` groups multiple member crates under one shared `Cargo.lock` and `target/` directory so they build together. `cargo publish` uploads to the registry, `cargo doc` renders rustdoc, and `build.rs` runs custom build scripts before compilation.
