---
tags: [seed, golang]
---

# Goroutines

A goroutine is a lightweight thread of execution managed by the Go runtime, launched by prefixing any call with the go keyword, as in go worker(ch). Goroutines start with a tiny few-kilobyte stack that grows and shrinks on demand, so a program can spawn hundreds of thousands of them. The runtime's M:N scheduler multiplexes goroutines (G) onto OS threads (M) across logical processors (P) set by GOMAXPROCS, parking a goroutine that blocks on a channel or syscall and reusing its thread for others. Goroutines coordinate through channels and the select statement rather than shared locks, though sync.Mutex and sync.WaitGroup remain available; wg.Add, go, and wg.Wait fan out and join work. Because main returning terminates every goroutine abruptly, you synchronize shutdown explicitly, and the go run -race detector flags data races on shared variables that escape a single goroutine.
