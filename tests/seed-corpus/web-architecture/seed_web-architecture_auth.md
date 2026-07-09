---
tags: [seed, web-architecture]
---

# Authentication and authorization

Authentication proves who a user is; authorization decides which resources and scopes they may reach. Signed JWTs carry claims in a header-payload-signature triad, verified against a secret or RS256 public key, while opaque session cookies pin identity to a server-side session store keyed by a session ID. OAuth 2.0 and OpenID Connect delegate login to an identity provider through the authorization-code flow, exchanging a short-lived access token plus a refresh token at the token endpoint. Bearer tokens ride the Authorization header; cookies should be marked HttpOnly, Secure, and SameSite to blunt XSS and CSRF. Role-based and attribute-based access control gate each endpoint, and the API gateway or auth middleware validates the token, checks expiry and audience, and rejects with 401 for missing credentials or 403 for insufficient privilege before any handler runs.
