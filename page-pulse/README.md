# Page Pulse

Page Pulse is an API endpoint that fetches a given URL and returns a structured health report containing metrics like response time, heading structure, and missing alt text. It audits server-rendered HTML only and does not execute JavaScript or render Single Page Applications (SPAs).

## Setup

```bash
git clone <repo>
cd page-pulse
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Running tests:**
```bash
pip install -r requirements-dev.txt
pytest -v tests/test_audit.py
```

**Live URL:**
*(Insert live Render URL here once deployed)*

## API Contract

**Endpoint:** `POST /api/audit`

### Request Shape
```json
{
  "url": "https://example.com"
}
```

### Response Shape (Success - 200 OK)
```json
{
  "url": "https://example.com",
  "final_url": "https://example.com/",
  "status_code": 200,
  "response_time_ms": 145,
  "content_type": "text/html; charset=utf-8",
  "title": "Example Domain",
  "meta_description": null,
  "h1_count": 1,
  "images_total": 0,
  "images_missing_alt": 0,
  "word_count": 28,
  "scanned_at": "2024-05-12T14:32:01Z"
}
```

### Error Response Shape
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description of what went wrong."
  }
}
```

### Error Codes
| Code | HTTP Status | Meaning |
|---|---|---|
| `INVALID_URL` | 400 | The URL is malformed or missing a valid hostname/scheme. |
| `PRIVATE_ADDRESS` | 400 | SSRF guard triggered. The URL resolves to a private, loopback, link-local, or multicast address. |
| `NON_HTML_RESPONSE` | 415 | The endpoint returned a content type other than `text/html`. |
| `RESPONSE_TOO_LARGE` | 413 | The response body exceeded the 5MB limit before parsing completed. |
| `TIMEOUT` | 504 | The server did not respond within the 10-second timeout. |
| `TOO_MANY_REDIRECTS` | 502 | The URL redirected more than 5 times. |
| `CONNECTION_FAILED` | 502 | DNS resolution failed, connection was refused, or a TLS error occurred. |
| `UPSTREAM_ERROR` | 502 | An unexpected error occurred while processing the URL. |

## Design Decisions

- **SSRF guard blocks private/loopback addresses before fetching.**
  A server that fetches arbitrary user-supplied URLs is a classic Server-Side Request Forgery (SSRF) vector. Without this guard, an attacker could point Page Pulse at `169.254.169.254` or an internal service and use the application to probe our own infrastructure. This adds a DNS resolution step before every request, slightly increasing latency on the happy path, but it is an essential security requirement for a tool that behaves like a proxy.

- **Word count strips `<nav>`, `<footer>`, `<header>`, `<script>`, and `<style>` before counting.**
  A raw text-node word count is dominated by navigation links and boilerplate on most real sites, making the metric virtually meaningless for judging actual content depth. While this is merely a heuristic and not a true content-extraction algorithm (like Mozilla's Readability)—it will still overcount on pages with heavy sidebar/widget content—it provides a significantly more accurate measure of the main text than a naive count.

- **Consistent error envelope across every failure mode, with a fixed enum of `code` values.**
  The application returns `{error: {code, message}}` regardless of the failure reason. A frontend (or any other consumer) can switch on `code` reliably without string-matching messages. The message text is for humans, while the code is strictly for programs. Maintaining this enum requires a bit more effort as new failure modes are discovered, but it yields a robust and stable API contract.

## Known Limitations

- **No JavaScript rendering:** SPAs (Single Page Applications) will report near-zero content since the tool only parses the initial HTML response.
- **No caching:** Every request fetches the target URL from scratch. Repeated scans of the same URL re-fetch every time.
- **No rate limiting:** Single-request rate limiting is not implemented at the application level, so a burst of requests to the same target domain is not throttled.
