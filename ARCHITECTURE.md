# Design / Architecture

## Goal
Provide a small embeddable lead-capture platform that a customer can paste into another website with one script tag. The capstone emphasizes backend reliability and security boundaries rather than a large frontend.

## Data model

- **Tenant**: customer boundary (`id`, `name`).
- **User**: demo authenticated owner (`tenant_id`, token). A production version should verify signed JWT/OIDC claims instead of storing demo tokens.
- **Widget**: `id`, `tenant_id`, `type`, `title`, `description`, `form_fields`, `button_text`, `display_options`, `allowed_origins`, `version`, timestamps.
- **Submission**: `id`, `widget_id`, submitted `data`, source `origin`, geo enrichment, timestamp. Tenant ownership is derived through the widget.

## Request paths

```text
OWNER --Bearer--> Widget CRUD --> tenant-isolated store
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
OWNER --Bearer--> dashboard submissions + stats
```

## API contract

Authenticated owner endpoints use `Authorization: Bearer <token>`. Public config and bundle endpoints expose only fields needed by the widget. Public submission accepts `{widget_id, data, website_origin, hp}` and returns a submission id on success.

## Non-goal

This capstone does **not** attempt to become a full form-builder SaaS: no visual editor, billing, production CDN, multi-region deployment, or advanced CAPTCHA is required.

## Reliability decisions

1. Store the submission before running the notification side effect.
2. Geo enrichment is best-effort and has deterministic fallback switches for proof.
3. Public assets use long-lived versioned bundle caching; config is short-lived.
4. Invalid/oversized payloads return JSON 4xx errors instead of reaching business logic.
