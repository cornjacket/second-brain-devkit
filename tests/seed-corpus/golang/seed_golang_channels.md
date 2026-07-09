---
tags: [seed, golang]
---

# Channels

Channels are typed conduits that pass values between goroutines, providing synchronization by communication rather than shared memory. Unbuffered channels block until both sender and receiver are ready. Closing a channel signals completion to receivers ranging over it.
