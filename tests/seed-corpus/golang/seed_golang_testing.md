---
tags: [seed, golang]
---

# Testing in Go

The testing package drives Go's built-in test tooling: go test compiles and runs every function named TestXxx(t *testing.T) in files ending _test.go, reporting failures through t.Errorf, t.Fatalf, and t.Helper. The idiomatic style is table-driven, iterating over a slice of anonymous structs holding name, input, and want fields and calling t.Run(tc.name, ...) so each case becomes a named subtest with granular pass/fail output and parallelism via t.Parallel. Benchmarks named BenchmarkXxx(b *testing.B) loop b.N times and report with go test -bench, while example functions named ExampleXxx are compiled and their // Output: comments verified. Fuzz targets FuzzXxx(f *testing.F) use f.Add seeds and go test -fuzz to explore inputs. Coverage comes from go test -cover, and t.Cleanup registers teardown. External packages use the xxx_test package suffix for black-box testing, and go test -race layers the data-race detector over the run.
