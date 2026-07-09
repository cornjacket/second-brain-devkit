---
tags: [seed, golang]
---

# Channels

Channels are typed conduits declared with make(chan T) that pass values between goroutines, embodying the maxim "share by communicating, don't communicate by sharing." An unbuffered channel is a synchronous rendezvous: the send ch <- v blocks until another goroutine executes the receive v := <-ch. A buffered channel, make(chan T, n), accepts up to n elements before the sender blocks, decoupling producer from consumer. Closing with close(ch) signals no further sends; receivers ranging with for v := range ch drain remaining buffered values then exit, and the comma-ok form v, ok := <-ch reports ok == false once drained. Sending on a closed channel panics, and a nil channel blocks forever. The select statement multiplexes several channel operations, firing whichever case is ready, with a default clause for non-blocking sends and receives. Directional types chan<- and <-chan constrain a channel's use in function signatures.
