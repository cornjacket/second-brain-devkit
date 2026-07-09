---
tags: [seed, golang]
---

# Error handling

Go treats errors as ordinary values of the built-in error interface, whose single method Error() string returns a message, returned as the last result alongside the successful value and checked explicitly with if err != nil. There is no try/catch; control flow stays linear. You construct errors with errors.New or fmt.Errorf, and wrapping with the %w verb, as in fmt.Errorf("open config: %w", err), records a cause chain that errors.Unwrap walks. errors.Is compares against a sentinel such as io.EOF or os.ErrNotExist through that chain, while errors.As extracts a concrete error type into a target pointer for inspecting structured fields. Custom error types implement Error() and often an Unwrap() method to participate in the chain. The idiom of returning early on err != nil, sometimes with a naked return of the zero value, keeps the happy path unindented and makes every failure site explicit at the call boundary.
