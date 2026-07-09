---
tags: [seed, web-architecture]
---

# REST APIs

A REST API models resources as URIs manipulated through HTTP verbs: GET reads, POST creates, PUT and PATCH update, and DELETE removes, each returning a status code — 200 OK, 201 Created, 204 No Content, 400 Bad Request, 401, 404 Not Found, or 500 — that tells the client what happened. GET, PUT, and DELETE are idempotent and GET is safe, so retries and caching are well defined, while POST is neither. Resources are exchanged as JSON representations, with content negotiation via the Accept and Content-Type headers. Statelessness means each request carries its own auth token and context so any server instance behind the load balancer can serve it. Good design uses noun-based collection and item paths, nests sub-resources, versions the API, paginates large collections with cursor or offset parameters, and returns consistent error envelopes. HATEOAS hyperlinks and ETag-based conditional requests round out a mature, self-describing interface.
