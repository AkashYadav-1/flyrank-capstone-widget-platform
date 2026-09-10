# FlyRank Embeddable Widget & Lead-Capture Platform

Backend capstone for the FlyRank Internship using **Python + FastAPI**. The platform provides tenant-isolated widget CRUD, an embeddable versioned JavaScript widget, cross-origin lead capture, abuse protection, geo fallback, failure-safe notification, and dashboard analytics.

The assignment asks for a separate public repository, honest incremental history, a run command plus seed step, `README.md`, `capstone.yaml`, `EVIDENCE.md`, `BUILDLOG.md`, and `.env.example`.

## Architecture

```text
Owner --Bearer--> Widget CRUD --> tenant-isolated store
                         |
                         +--> embed snippet --> versioned widget.js
Customer site :5500 ----+--> cached config --> POST /submissions
                                               |
                                  validation + CORS + rate limit + honeypot
                                               |
                                  geo A -> geo B -> no geo -> store
                                               |
                                  non-critical notification
                                               |
Owner --Bearer--> dashboard submissions + stats
```

See `ARCHITECTURE.md` for the detailed model, contracts, and non-goal.

## Run locally

### Option A — Docker (recommended)

```bash
copy .env.example .env
python seed.py
docker compose up --build
```

API: `http://localhost:8000/docs`

### Option B — Python directly

```bash
copy .env.example .env
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload --port 8000
```

## Demo credentials

`seed.py` creates two demo tenants:

- Tenant A: `Bearer demo-token-a`
- Tenant B: `Bearer demo-token-b`

These are local demo credentials only and are never committed as secrets. `.env` and runtime `data.json` are ignored by Git.

## Customer-site test

Start the API, then in a second terminal:

```bash
python -m http.server 5500 --directory customer
```

Open `http://localhost:5500`. The page is deliberately a different origin from the API.

## API

| Method | Endpoint | Auth |
|---|---|---|
| POST | `/auth/login` | no |
| POST | `/widgets` | owner |
| GET | `/widgets` | owner |
| GET/PUT/DELETE | `/widgets/{id}` | owner |
| GET | `/widgets/{id}/embed` | owner |
| GET | `/widgets/{id}/config` | public |
| GET | `/widget.v{version}.js?id={id}` | public |
| OPTIONS | `/submissions` | public |
| POST | `/submissions` | public |
| GET | `/dashboard/submissions` | owner |
| GET | `/dashboard/stats` | owner |

## Acceptance behavior

- Widget CRUD requires valid bearer authentication and tenant ownership is checked on every lookup.
- Embed snippets point to a versioned bundle.
- Config returns `Cache-Control: public, max-age=60`; bundles use a one-year immutable cache.
- Submission preflight is handled by FastAPI CORS middleware.
- Payloads are validated by Pydantic; oversized bodies return 413; invalid fields return 422.
- Rate limiting is per IP + widget and returns 429 under a burst.
- The hidden `hp` field is a honeypot; a non-empty value is rejected.
- Geo enrichment follows provider A → provider B → no-geo. Environment switches make fallback proof deterministic.
- Notification failure is swallowed after storage, so the lead still succeeds.
- Dashboard endpoints aggregate only the authenticated owner's widgets/submissions.

## Limitations

This is intentionally a local, zero-cost capstone. Persistence is a small JSON repository so the project can run without a paid database. A production system should replace demo bearer tokens with signed JWT/OIDC verification, use PostgreSQL transactions, call real geo providers behind timeouts, and serve the immutable bundle through a CDN.

## Evidence

`EVIDENCE.md` is the evaluator proof map. Paste real command output for each requirement rather than claiming a feature exists.

## AI usage

`BUILDLOG.md` records where AI assisted, what was reviewed, and the important implementation decisions. The owner should be able to explain the authentication flow, tenant filter, CORS/preflight behavior, rate limiter, fallback chain, and failure-safe side effect.
