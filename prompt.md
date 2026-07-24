# PAGE PULSE — Build Spec for Antigravity

You are building "Page Pulse," a URL health-audit tool. Read this entire spec before writing any code. Follow it precisely — every detail here is intentional, not a suggestion.

---

## 1. THE CONCEPT (read this first — it drives every design decision below)

Page Pulse audits a URL and reports back its health. The name is "Pulse." So the product is not a "dashboard" or an "analyzer" — it is a **diagnostic chart**, the way a doctor's office produces a vitals printout. Every visual and copy decision should reinforce this metaphor *without ever becoming cutesy or literal (no stethoscope emoji, no cartoon heart icons)*. The medical framing shows up in structure and language, not decoration.

Concretely:
- The input screen is a **patient intake field** — one URL, one action.
- While the tool fetches the page, an **animated pulse-line (ECG-style waveform)** sweeps across the screen. This is not decorative filler: the waveform's amplitude and jitter are driven by real data once the response comes back (fast, healthy response → calm steady wave; slow or erroring response → irregular, spiking wave). Build it as an SVG polyline whose points are generated from actual response-time and status data, not a canned CSS animation.
- The results screen is a **chart / report printout**: a clear "vitals" section (status, response time, content type) followed by a "findings" section (title, meta description, H1 count, missing alt text, word count), each row styled like a chart entry — label, value, and a status indicator (stable / attention / critical), not just a plain key-value list.
- Overall severity is expressed as a single top-line read, like a chart summary line — not a gimmicky "score out of 100" badge.

Do not use the word "diagnosis" or medical jargon in the copy. The metaphor lives in structure and rhythm, not in words like "prognosis." Keep copy plain, direct, and in the interface's voice (see Section 5).

---

## 2. DESIGN TOKEN SYSTEM (follow exactly — do not substitute your own defaults)

**Explicitly avoid these three overused AI-generated looks: (1) warm cream background + high-contrast serif + terracotta/clay accent, (2) near-black background + single acid-green or vermilion accent, (3) broadsheet layout with hairline rules and zero border-radius. None of these are used here.**

### Color — "clinical paper" palette
- `--paper`: `#EEF0EA` — pale sage-white background (not cream, has a cool/green undertone)
- `--ink`: `#1B2521` — near-black ink with a green-black cast, used for all text
- `--grid`: `#D8DCD3` — faint graph-paper gridlines, used sparingly as a background texture on the report screen only
- `--pulse-critical`: `#E8483C` — coral-red, used ONLY for error/critical states and the pulse-line when things are bad
- `--pulse-stable`: `#1F7A5C` — deep clinical green, used for pass/healthy states
- `--pulse-attention`: `#C98A2C` — amber, for borderline/warning states (e.g. slow-but-not-timeout response)
- `--paper-raised`: `#F7F8F4` — slightly lighter than paper, for card surfaces

### Type
- Display face (headline, "Page Pulse" wordmark, report section labels): **IBM Plex Serif**, used at restrained weights — this gives the chart/report authority without being a generic display serif.
- Body face: **IBM Plex Sans** — clean, functional, for all descriptive copy.
- Utility/data face: **IBM Plex Mono** — used specifically for the URL itself, status codes, response-time numbers, and word counts. This is what makes the report read like real diagnostic data rather than prose.

Load all three from Google Fonts or self-host; do not substitute system fonts.

### Layout concept
- Single centered column, max-width ~640px, generous vertical rhythm — the report should feel like a printed sheet, not a dashboard grid.
- The intake screen: wordmark top-left (small, quiet), one large input field with a mono placeholder like `https://example.com`, one primary action button labeled "Run pulse" (not "Submit" or "Analyze").
- The report screen: URL and timestamp at top in mono type (like a chart header), then a "Vitals" block (status/response time/content type as three chart rows), then a "Findings" block (title/meta/H1/alt/word-count as chart rows), each row with a left-aligned label, right-aligned value, and a small status-color dot — no icons, no emoji.
- Loading state: the input screen morphs into the pulse-line animation directly in place — do not use a spinner or skeleton loader.

### Signature element
The data-driven pulse-line waveform, present in two places: (1) as the loading animation, and (2) as a persistent thin strip at the top of the finished report, replaying the actual waveform of that scan so the user can glance at it and read "healthy vs. rough" at a glance before reading a single number.

---

## 3. WHAT TO WRITE FOR COPY

Follow these rules (do not skip — generic copy is what makes AI builds look templated even with good visuals):
- Active voice, plain verbs, sentence case. No filler like "Welcome to Page Pulse! Let's get started."
- Errors state exactly what happened and, where possible, what to do — never vague, never apologetic. E.g. `"Couldn't reach this URL — the server didn't respond within 10s."` not `"Oops! Something went wrong."`
- Empty/idle state on the intake screen should read as a direct invitation: e.g. a single line under the input like `"Paste any public URL to run a pulse check."`
- Button labels name the action, not the mechanism: "Run pulse," not "Submit request."
- No exclamation points, no emoji, anywhere in the UI.

---

## 4. TECH STACK

- **Backend:** Python, FastAPI. Use FastAPI specifically (not Flask) — it gives automatic request validation and OpenAPI docs, which strengthens the API-design portion of this build with minimal extra code.
- **HTML parsing:** `httpx` for the fetch (supports timeouts and async cleanly) + `BeautifulSoup4` for parsing.
- **Frontend:** plain HTML/CSS/vanilla JS — no framework. A framework adds no value at this scale and vanilla JS keeps the SVG pulse-line animation fully under your control. Single `index.html`, one CSS file, one JS file. Serve the frontend as static files from the same FastAPI app (simplifies deployment to one service).
- **Deployment:** Render (free tier) for the combined FastAPI app serving both the API and the static frontend. One service, one URL. (Alternative: Railway free tier — pick whichever you already have an account on.)

---

## 5. BACKEND SPEC

### Endpoint: `POST /api/audit`

**Request body:**
```json
{ "url": "https://example.com" }
```

**Success response — `200 OK`:**
```json
{
  "url": "https://example.com",
  "final_url": "https://example.com/",
  "status_code": 200,
  "response_time_ms": 214,
  "content_type": "text/html",
  "title": "Example Domain",
  "meta_description": "This domain is for use in illustrative examples.",
  "h1_count": 1,
  "images_total": 4,
  "images_missing_alt": 1,
  "word_count": 312,
  "scanned_at": "2026-07-24T10:15:00Z"
}
```

**Error response shape (consistent across ALL failure modes):**
```json
{
  "error": {
    "code": "TIMEOUT",
    "message": "Couldn't reach this URL — the server didn't respond within 10s."
  }
}
```

Error `code` values to implement, each with its own precise message and correct HTTP status:
| code | HTTP status | Trigger | Message tone |
|---|---|---|---|
| `INVALID_URL` | 400 | Malformed URL, missing scheme, not http/https | State exactly what's wrong with the URL |
| `PRIVATE_ADDRESS` | 400 | URL resolves to a private/loopback/link-local IP (SSRF guard — see below) | "This URL points to a private address and can't be scanned." |
| `TIMEOUT` | 504 | Fetch exceeds a 10s timeout | As shown above |
| `CONNECTION_FAILED` | 502 | DNS failure, connection refused, TLS error | "Couldn't connect to this host." + underlying reason class (DNS/TLS/refused) |
| `NON_HTML_RESPONSE` | 415 | Content-Type isn't text/html (PDF, JSON, image, etc.) | State the content-type that was returned instead |
| `TOO_MANY_REDIRECTS` | 502 | >5 redirect hops | "This URL redirected more than 5 times." |
| `RESPONSE_TOO_LARGE` | 413 | Body exceeds 5MB before parsing completes | "This page is too large to audit." |
| `UPSTREAM_ERROR` | 502 | Any other unhandled fetch exception | Generic but non-crashing catch-all — log the real exception server-side, never leak a stack trace to the client |

**SSRF guard (important, do not skip):** before fetching, resolve the hostname and reject if it resolves to a private/loopback/link-local/multicast IP range (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8, 169.254.0.0/16, ::1, fc00::/7). This is a real correctness/security concern for a "fetch any URL server-side" tool and is worth calling out explicitly in the README as a design decision.

### Metric extraction logic
- `response_time_ms`: measured server-side around the actual fetch call, not including your own processing time.
- `title`: `<title>` tag text, trimmed. `null` if absent — do not default to empty string (the frontend should render this as a distinct "not found" row, not a blank one).
- `meta_description`: `<meta name="description" content="...">`. `null` if absent.
- `h1_count`: count of `<h1>` tags in the parsed DOM.
- `images_total` / `images_missing_alt`: count all `<img>` tags; "missing alt" = the `alt` attribute is absent OR is an empty/whitespace-only string.
- `word_count`: strip `<script>`, `<style>`, `<nav>`, `<footer>`, `<header>` before counting — otherwise boilerplate inflates the number. Split on whitespace after stripping tags. (Call this design decision out explicitly in the README — it's a real judgment call, not an edge case.)

### Never crash
Every exception path must resolve to one of the error codes above with a 4xx/5xx status and the standard error JSON shape. Wrap the whole handler in a top-level try/except that falls through to `UPSTREAM_ERROR` as a last resort — the server should never return a raw 500 with no body or an unhandled traceback.

---

## 6. FRONTEND SPEC

**States:** idle → loading → success → error. Each is a distinct visual state, not just conditional text.

- **Idle:** intake screen as described in Section 2. Input has real client-side validation (must look like a URL) before the request fires, with the same plain-language error style as the backend.
- **Loading:** input field area transitions into the pulse-line SVG animation in place (no layout jump). A quiet mono-type status line beneath it: `"Scanning [url]..."`.
- **Success:** report screen as described in Section 2, replaying the real waveform, followed by vitals and findings blocks. Each finding row shows a status dot: green (`--pulse-stable`) for good, amber (`--pulse-attention`) for borderline (e.g. 1-2 images missing alt, meta description missing), red (`--pulse-critical`) for clearly bad (e.g. no H1, no title, many images missing alt). Define the thresholds explicitly in code, not arbitrarily in markup.
- **Error:** report screen replaced with a single clear error card — the message from the backend's `error.message`, styled with the `--pulse-critical` accent, plus a "Try another URL" action that returns to idle.

**Accessibility (do not skip):** visible keyboard focus states on the input and button, sufficient color contrast (verify ink-on-paper and all status colors against WCAG AA), respect `prefers-reduced-motion` by replacing the pulse-line animation with a static version of the same waveform when that media query is set.

**Responsive:** must work cleanly down to a 375px-wide mobile viewport — the report rows should stack label-above-value on narrow screens rather than truncating.

---

## 7. MANDATORY FOOTER CREDIT LINE

Add to the footer of the deployed page, visible without scrolling on the report screen:

```html
<footer>
  <a href="https://digitalheroesco.com" target="_blank" rel="noopener">Built for Digital Heroes Training Task</a>
</footer>
```

Style this quietly — small, muted color, bottom of page — it should read as a footnote, not a badge. Do not let it disrupt the clinical-paper aesthetic (e.g. no logo, no colored button styling around it).

---

## 8. FILE STRUCTURE

```
page-pulse/
├── app/
│   ├── main.py          # FastAPI app, static file mount, /api/audit route
│   ├── audit.py         # fetch + parse + metric extraction logic
│   ├── errors.py         # error code definitions and exception→response mapping
│   └── ssrf_guard.py     # hostname resolution + private-IP check
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js            # fetch call, state transitions, pulse-line SVG generation
├── requirements.txt
├── render.yaml            # or equivalent deploy config
└── README.md              # (Task B — not covered in this spec)
```

---

## 9. THINGS TO EXPLICITLY NOT DO

- Do not use a component framework, CSS utility framework, or UI kit — hand-build the CSS from the token system above.
- Do not add icons, emoji, gradients, drop shadows, or glassmorphism — the aesthetic is flat, paper-like, precise.
- Do not add a "score out of 100" badge or gamified grading — this is a chart, not a game.
- Do not use a canned spinner/skeleton loader for the loading state — use the data-aware pulse-line as specified.
- Do not let any backend exception surface as an unhandled 500 or raw traceback to the client.
- Do not hardcode the footer credit line styling to stand out — it must look like a natural footnote.

---

Build in this order: SSRF guard → audit/parsing logic → error handling → FastAPI route + OpenAPI schema → static frontend shell (idle state) → pulse-line SVG generator → loading/success/error state wiring → responsive + accessibility pass → deploy → verify the live URL end to end with a real slow site, a real 404, and a real non-HTML URL (e.g. a PDF link) before calling it done.