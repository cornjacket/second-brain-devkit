---
tags: [seed, golang]
---

# Goroutines

A goroutine is a lightweight thread managed by the Go runtime, started with the go keyword and multiplexed onto OS threads. They are cheap enough to launch thousands. The runtime scheduler handles blocking calls without tying up an OS thread.
