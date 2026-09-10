# BUILDLOG

## 2026-09-10 — Capstone implementation

- Chose Python + FastAPI because it matches the backend track and keeps the service easy to run locally.
- Kept the public HTTP contract independent from persistence so the demo can use a JSON repository while a PostgreSQL repository can be substituted later.
- Implemented authenticated widget CRUD and enforced tenant ownership in the data access path rather than trusting UI filtering.
- Added versioned widget JS and short-lived config caching with explicit `Cache-Control` headers.
- Added CORS/preflight, payload size protection, Pydantic validation, per-IP/widget rate limiting, and a hidden honeypot field.
- Implemented deterministic geo provider A → B → no-geo fallback switches for evaluator-friendly tests.
- Made the notification side effect non-critical: persistence happens first and side-effect errors are logged without changing the successful response.
- Added dashboard aggregate endpoints and a plain HTML second-origin customer page.

## Test review / corrections

- The first local test expected the explicit OPTIONS handler to return 204, but FastAPI's CORS middleware correctly handled the browser-style preflight as 200. The test was corrected to assert successful preflight plus the CORS header rather than over-constraining the status code.
- Final local test suite: **6 passed**.

## AI assistance

AI was used as a coding assistant to draft route structure, validation models, documentation, and test-plan wording. The implementation was reviewed and adjusted to match the capstone brief. The owner should be able to explain the authentication flow, tenant filter, CORS/preflight behavior, rate limiter, fallback chain, and failure-safe side effect.
