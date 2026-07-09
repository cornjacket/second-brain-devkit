---
tags: [seed, web-architecture]
---

# Three-tier architecture

The three-tier architecture splits a web application into a presentation tier, an application tier, and a data tier, each deployable and scalable on its own. The presentation tier is the browser client rendering HTML, CSS, and JavaScript that issues HTTP requests to the backend. The application tier holds the business logic in a web or application server — behind a reverse proxy and load balancer — where request handlers, authentication, and the domain model live and where a stateless design lets the tier scale out horizontally across instances. The data tier is the persistence layer of relational or NoSQL databases, often fronted by a caching layer and served through read replicas. Tiers communicate only across defined interfaces, so the presentation tier never touches the database directly; this separation of concerns localizes change, lets each tier scale independently, and hardens the trust boundary between the public frontend and the private backend network.
