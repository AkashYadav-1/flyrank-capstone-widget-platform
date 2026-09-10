# EVIDENCE

## Local verification run

Command:

```text
PYTHONPATH=. pytest -q
```

Output:

```text
......                                                                   [100%]
6 passed in 0.34s
```

The automated suite covers authenticated CRUD and tenant isolation, embed/config/versioned bundle delivery, CORS preflight, malformed payload validation, oversized payload rejection, honeypot spam blocking, rate limiting, geo fallback including all-providers-down success, failure-safe side effects, and tenant-scoped dashboard results.

## Acceptance proof map

| Requirement | Proof / command |
|---|---|
| Authenticated CRUD | `tests/test_capstone.py::test_auth_crud_and_tenant_isolation` — 6-test suite passes |
| Tenant isolation | Same test proves tenant B receives 404 for tenant A widget and dashboard is scoped |
| Embed snippet | `test_config_embed_and_versioned_bundle` |
| Cached config | Test asserts `Cache-Control` contains `max-age=60` |
| Versioned JS | Test asserts immutable cache header on `/widget.v1.js` |
| CORS preflight | `test_cors_validation_oversize_and_honeypot` asserts successful preflight and allow-origin header |
| Validation | Same test expects 422 for missing required field |
| Oversized payload | Same test expects 413 for >10 KB payload |
| Rate limiting | `test_rate_limit_returns_429` sends 20 accepted requests then expects 429 |
| Honeypot | Same test expects 400 when `hp` is populated |
| Geo fallback | `test_geo_fallback_and_all_down_still_succeeds` proves A→B and A+B down paths |
| Safe side effect | `test_side_effect_failure_does_not_block_and_dashboard_is_tenant_scoped` expects 201 with simulated notification outage |
| Dashboard | Same test checks authenticated stats and tenant scope |
| Second origin | `customer/index.html` is served on port 5500 while API runs on 8000 |

## Manual browser gate

Run:

```text
python -m http.server 5500 --directory customer
```

Then open `http://localhost:5500`. The page loads the API's versioned widget script from port 8000 and exercises cross-origin config and submission behavior.

## Deterministic failure switches

- `GEO_PROVIDER_A_DOWN=1` forces provider B.
- `GEO_PROVIDER_B_DOWN=1` together with A down stores the submission without geo.
- `SIDE_EFFECT_DOWN=1` simulates notification failure while keeping the main submission successful.

No real API keys, passwords, tokens, or `.env` files are committed.
