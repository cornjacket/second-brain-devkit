---
tags: [seed, web-architecture]
---

# WebSockets

WebSockets upgrade an ordinary HTTP request via the Upgrade header and 101 Switching Protocols handshake into a persistent, full-duplex TCP connection over the ws or wss scheme, so client and server exchange framed messages in both directions without the overhead of repeated polling or long-polling. This long-lived socket suits chat, live dashboards, multiplayer collaboration, and push notifications where the server initiates delivery. Ping-pong control frames and heartbeats keep the connection alive through idle timeouts and detect half-open sockets. Horizontal scaling is harder because a connection is bound to one server instance: a reverse proxy must support the upgrade and use sticky routing, and fan-out across nodes needs a Redis or message-broker pub/sub backplane so a message published on one instance reaches subscribers pinned to another. Clients reconnect with exponential backoff, and higher-level libraries add rooms, channels, and automatic fallback to HTTP transports.
