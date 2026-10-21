# LifeLens Ω — Design Document

> **Status:** Feature-complete prototype · Phases A–L complete · 287/287 tests passing
> **Design System:** Passport Control
> **Philosophy:** Institutional solemnity, reality verification over accusation, physical document-inspection metaphor — zero artificial web-template clichés.

---

## 1. What Is LifeLens Ω?

LifeLens Ω is a **privacy-aware, multi-modal reality integrity and trust verification system** for foreign job offers, recruiter communications, and live meeting authenticity. It deliberately avoids returning black-box verdicts ("SCAM / SAFE") and instead produces an **auditable Entity → Claim → Evidence ledger** evaluated through the four-pillar **CECT Reasoning Framework** — Coherence, Evidence Independence, Consistency, Trajectory.

> *"Built with the belief that people deserve evidence, not verdicts, before they trust, pay, or travel."*

### Core Problem

| Stat | Source |
|---|---|
| Employment scams reported to FBI IC3 in 2025 | 48,000+ cases, $330M+ in losses |
| Job scam losses, 2023 | $367M (FTC) |
| Job seekers who encounter a scam | ~1 in 7 |
| Fake / ghost job postings | ~27–43% of listings |

Existing tools only check language patterns. LifeLens Ω checks the thing that actually matters: **is the claim independently verifiable?**

---

## 2. Product Principles

| # | Principle | In Practice |
|---|---|---|
| P1 | Verification over accusation | `Needs Verification` or `High Risk`, never `SCAMMER` |
| P2 | Signal ≠ Proof | "Uses Gmail" → *domain mismatch, verify further* — never *is fraudulent* |
| P3 | Evidence needs provenance | Every finding states what / where / when was checked and source reliability |
| P4 | No fake metrics | Every number labeled `TARGET`, `BENCHMARK`, `MEASURED`, or `ILLUSTRATIVE` |
| P5 | Privacy by default | Only data needed for job/recruiter/company verification is collected |
| P6 | Human-in-the-loop | The system explains; the person chooses: verify, continue, report, or stop |

---

## 3. Design System — Passport Control

The Passport Control design language evokes the gravity and tactile authority of border-inspection desks, stamped consular visas, and physical audit ledgers. It intentionally avoids contemporary SaaS template tropes.

### 3.1 Colour Palette

| Token | Hex | Semantic Usage & Invariants |
|---|---|---|
| `--ink` | `#1B2A4A` | Primary base, structural borders, headers, primary buttons, high-contrast framing |
| `--paper` | `#F7F5F0` | Primary application canvas, body background, neutral container fill |
| `--paper-card` | `#FFFFFF` | Document cards, ledger slips, active inspection panels |
| `--graphite` | `#2A2A28` | Body text, readable labels, high-legibility dark foreground |
| `--graphite-muted` | `#5A5A58` | Secondary labels, metadata descriptions, timestamps |
| `--stamp-red` | `#B8433D` | **STRICT INVARIANT:** Reserved exclusively for flagged risks, blocked SSRF, and critical alerts |
| `--stamp-green` | `#3D6B4F` | **STRICT INVARIANT:** Reserved exclusively for verified claims, passing checks, and active protection |
| `--amber` | `#9C6B1F` | **STRICT INVARIANT:** Reserved exclusively for unverified claims, partial evidence, and `[SIMULATED]` badges |
| `--border` | `#D5D2C8` | Tactile card borders, ledger dividing rules, field enclosures |

### 3.2 Typography Hierarchy

| Role | Font | Weight | Usage Rule |
|---|---|---|---|
| Headings & Display | `Fraunces` (Serif, variable optical 9–144) | 600 | Legal/institutional credibility; page titles, stamp labels, verdict headlines |
| Body & UI Controls | `Inter` (Sans-Serif) | 400 / 500 / 600 | All readable UI text, form labels, navigation, paragraphs |
| Evidence Data & Hashes | `JetBrains Mono` (Monospace) | 400 / 600 | **STRICT INVARIANT:** Only evidence hashes, cryptographic signatures, IP addresses, timers, and timestamps |

Fonts loaded via Google Fonts with native system-serif / system-sans / monospace fallback chains.

### 3.3 Animation Rule — The Rotated Stamp

- The rotated verdict seal (`transform: rotate(-4deg)`) is the **sole** animated transition permitted across the application.
- All scroll-reveal motion, bouncy spring physics, continuous pulsating glows, and parallax effects are **prohibited**.

### 3.4 Banned Template Tells (Zero Tolerance)

1. NO tracked-out ALL-CAPS eyebrows — No `letter-spacing: 0.25em` decorative sub-headers.
2. NO middle-dot meta strings — No `·` or `•` separating metadata fragments.
3. NO trailing arrows — No `→` or `->` appended to buttons or links.
4. NO gradient washes — Flat, rich `#1B2A4A` ink-blue and `#F7F5F0` paper only.
5. NO identical rounded-card grids — Layouts reflect distinct document and ledger proportions.
6. NO glassmorphism — Zero `backdrop-filter: blur()`; physical opaque surfaces only.

---

## 4. Surface Inventory

LifeLens Ω ships across **four distinct surfaces**, each with its own constraints and file locations.

### 4.1 Chrome Extension (Manifest V3)

**Directory:** `apps/extension/`

```
apps/extension/
├── manifest.json           — MV3 manifest (permissions, content_scripts, side_panel)
├── package.json
└── src/
    ├── background/         — Service worker (message routing, API proxy)
    ├── content/            — DOM inspector injected into LinkedIn, Indeed, Reed, Glassdoor
    ├── sidepanel/          — Primary result UI (sidepanel.html / sidepanel.js / sidepanel.css)
    ├── popup/              — Minimal toolbar popup
    ├── components/         — Shared UI components (evidence cards, risk badges)
    ├── services/           — API client, claim extractor, normalizer
    └── types/              — Shared TypeScript-style JS types
```

**CSP Compliance (MV3 Strict):**
- **Zero remote code** — No `<script src="https://...">` tags; all logic bundled locally.
- **Zero inline code** — No inline `<script>` blocks or `onclick="..."` attributes.
- **Self-hosted assets** — All stylesheets bundled in `sidepanel.css`; fonts fall back to system families.

What the content script does: Inspects the DOM of supported job boards and extracts structured employer claims (Company, Recruiter, Website, Job Title, Description) — only the fields required for verification. Zero raw page-scraping telemetry leaves the browser.

### 4.2 Web Workspace UI

**Directory:** `apps/web/`

```
apps/web/
├── index.html              — Single-page workspace (64 KB; all 7 screens embedded)
├── styles.css              — Passport Control design system (19 KB)
├── app.js                  — Interactive verification, API calls, screen orchestration (25 KB)
└── manifest.webmanifest    — PWA manifest
```

Served at `http://localhost:8000/` directly from the FastAPI backend via static file mount. Contains all seven specified screens as distinct named sections navigable by fragment ID.

### 4.3 Desktop Call Guard (Tauri)

**Directory:** `apps/desktop/`

```
apps/desktop/
├── src/                    — HTML/CSS/JS frontend (index.html, floating HUD)
└── src-tauri/              — Rust Tauri shell (always-on-top window, tray, OS hooks)
```

**Window spec:** 460 x 660 px, always-on-top capable, frameless floating HUD. Communicates with the backend via local WebSocket / HTTP.

### 4.4 FastAPI Backend & API

**Directory:** `apps/api/app/`

```
apps/api/app/
├── main.py                 — FastAPI entry point, CORS, static mount, router registration
├── api/                    — Route handlers (v1_verification.py, call_guard, meeting_shield, ledger)
├── cect/                   — CECT reasoning engine (coherence, independence, consistency, trajectory)
├── detectors/              — 7 specialized detectors (code scanner, digital arrest, voice clone, quishing)
├── explanations/           — Plain-language explanation generator
├── integrations/           — Platform integration adapters (Zoom, Meet, Teams, WhatsApp, Telegram, Webex)
├── models/                 — Canonical domain models (Entity, Claim, Evidence, LedgerBlock)
├── repositories/           — SQLAlchemy ORM models & CRUD repositories
├── risk/                   — Risk & confidence assessment engine
├── schemas/                — Pydantic v2 API request/response schemas
├── security/               — SSRF Shield (blocks RFC 1918, loopback, link-local, cloud metadata)
├── services/               — Extractor, normalizer, trust graph, verification orchestrator
└── verification/           — Source adapters (Companies House, SEC EDGAR, India MCA, UAE NER, WHOIS/RDAP)
```

---

## 5. Seven Screen Specifications

### Screen 1 — Pre-Call Invite Result (Layer 0 Link Inspector)

**Surface:** Extension sidepanel (`apps/extension/src/sidepanel/`) · Web workspace `#callguard`
**Endpoint:** `POST /api/v1/call-guard/invite/check`

**Layout:**
- Ink-blue (`#1B2A4A`) header strip with `LIFELENS Ω` mono seal in JetBrains Mono.
- Plain input fields with tactile `#D5D2C8` borders — no gradient fills.
- Stamp seal positioned at top-right of result card (`VERIFIED`, `UNVERIFIED`, or `FLAGGED`).
- Signal provenance rows detailing `what`, `where`, `when`, and `source_reliability`.
- Actionable out-of-band verification steps checklist (always visible, not collapsible).

**Verdict states:**
- `VERIFIED` — green stamp, `#3D6B4F`.
- `UNVERIFIED` — amber pill `#9C6B1F`.
- `FLAGGED` — red stamp `#B8433D`.

---

### Screen 2 — Desktop Guard HUD ("Guard is ON" State)

**Surface:** Tauri Desktop Floating Window (`apps/desktop/src/index.html`)
**Window:** 460 px wide x 660 px tall, always-on-top.

**Components:**
- Top status bar with `#3D6B4F` `GUARD IS ON` pill (JetBrains Mono text, no letter-spacing).
- Prominent, stamp-red (`#B8433D`) one-click **Stop** button — instant kill-switch, never hidden.
- Platform selector: Zoom · Meet · Teams · WhatsApp · Telegram · Webex.
- Ephemeral in-memory transcript stream feed with local ASR latency indicator (`LATENCY: < 15ms`).
- No raw audio or transcript data is persisted to disk at any point.

---

### Screen 3 — High-Risk Interstitial (Callback Checklist & Cooling-Off Timer)

**Surface:** Layer 3 Overlay Modal (`apps/desktop/src/index.html#interstitialModal`)

**Components:**
- Solid `#1B2A4A` overlay backdrop with high-contrast paper card and stamp-red border.
- `HIGH-RISK DETECTED` rotated stamp (`rotate(-4deg)`, `#B8433D`).
- Payment cooling-off countdown timer — `15:00` digits rendered in JetBrains Mono.
- 3-step independent callback verification checklist with interactive checkboxes:
  1. Mute call / tell caller you will call back.
  2. Look up official number in an independent directory.
  3. Verify identity via pre-agreed code word.
- Pre-agreed code word display box (`SHIELD-2026-ALPHA`).
- **Dismiss** / **Hang Up** buttons — human-in-the-loop decision gate (P6). No auto-action.

---

### Screen 4 — Liveness Challenge Coach

**Surface:** Layer 4 Coach Drawer (`apps/desktop/src/index.html#coachBar`)

**Components:**
- Drawer (slides up from bottom; sole permitted transition is the stamp animation).
- Four physical liveness challenges displayed as numbered ledger rows:
  1. Turn head 90 degrees to profile — exposes 2D warping.
  2. Pass open hand across mouth and nose — disrupts neural bounding box.
  3. Hold up a random physical object next to cheek.
  4. Repeat a random, unpredictable sentence.
- **Compliance disclaimer** (always visible): *"The app never claims a pass/fail verdict — you observe the caller's reaction and decide (P6)."*

---

### Screen 5 — Participant Independence Panel

**Surface:** Web workspace `#independencePanel` · Desktop inspector
**Implements:** Rule C — Shared-Origin Evidence Independence

**Components:**
- Visual cluster grouping UI demonstrating Rule C:
  - Shows N attendees grouped under a single origin bracket (e.g., `[Invite Link #9821]`).
  - Collapses N vouchers into: `Effective Independent Sources: 1`.
  - Highlights Rule C blocker: *"At least one independently verified participant is required for verified-trust."*
- Provenance tag per attendee: guest join time, account window, origin ID.
- No participant names stored beyond the active session.

---

### Screen 6 — Post-Call Receipt

**Surface:** Post-Call View (`apps/desktop/src/index.html#receiptCard`)
**Endpoint:** Session end via `POST /api/v1/meeting-shield/session/{id}/end`

**Components:**
- Physical receipt border styling (dashed `--border` rule, `--paper-card` fill).
- Rotated `VERIFIED RECEIPT` green stamp (`#3D6B4F`, `rotate(-4deg)`).
- Session metadata: duration, platform, start/end timestamps (JetBrains Mono).
- List of detected requests (transfer, remote access, credential ask) — each with severity tag.
- Completed verification checklist items with checkmarks.
- Cryptographic SHA-256 HMAC ledger entry hash (`0x...` in JetBrains Mono).
- **Explicit data-deletion confirmation:** *"Zero raw audio or video was persisted. Transcript purged from memory."*

---

### Screen 7 — `[SIMULATED]` Badge Treatment

**Surface:** Web workspace · API Swagger · Extension result cards
**Implements:** P4 — No fake metrics

**Treatment:**
- Amber badge: `color: #9C6B1F`, `background: rgba(156,107,31,0.12)`, `border: 1px solid #9C6B1F`.
- Font: JetBrains Mono, label text: `[SIMULATED]`.
- Tooltip/disclaimer always present: *"Simulated offline provider. Contributes 0 weight to verification evidence (P4)."*
- Applied to all mock registry responses — their `risk_boost` is clamped to `0.0`.

---

## 6. Core Data Model

The entire reasoning system is grounded in a formal **Entity → Claim → Evidence** hierarchy.

```
VerificationRequest
    ├── Entity[]             (COMPANY | RECRUITER | DOMAIN)
    │     └── Claim[]        (IDENTITY | EMPLOYMENT | SALARY | VISA | PAYMENT | URGENCY | ...)
    │           └── Evidence[]   (BUSINESS_REGISTRY | DOMAIN_REGISTRY | OFFICIAL_WEBSITE | ...)
    └── CECTAssessment
          └── RiskAssessmentResult
                └── ExplanationReport
```

### Key Model Fields (Python dataclasses)

**`VerificationRequest`** — `request_id`, `job_title`, `company_name`, `company_website`, `recruiter_email`, `claimed_country`, `job_description`, `source_platform`, `consent_for_analysis`

**`Entity`** — `entity_id`, `entity_type`, `claimed_name`, `normalized_name`, `verification_status` (`UNKNOWN | PARTIALLY_VERIFIED | VERIFIED | CONTRADICTED | UNAVAILABLE`), `verification_confidence` (0.0–1.0)

**`Claim`** — `claim_id`, `entity_id`, `claim_type` (`IDENTITY | EMPLOYMENT | SALARY | VISA | PAYMENT | DOCUMENT | URGENCY | CONTACT | WEBSITE ...`), `verification_status`, `supporting_evidence_ids[]`, `contradicting_evidence_ids[]`

**`Evidence`** — `evidence_id`, `source_type`, `source_name`, `observed_value`, `captured_at`, `source_authority` (0.0–1.0), `source_independence` (0.0–1.0), `user_verifiable` (bool), `verification_path` (URL), `evidence_strength`, `source_status` (`AVAILABLE | UNAVAILABLE | STALE | CONFLICTING`)

**`LedgerBlock`** (Phase 5) — `index`, `timestamp`, `request_id`, `entity_name`, `risk_level`, `confidence`, `evidence_hashes[]`, `previous_hash`, `block_hash` — SHA-256 hash-chained append-only audit trail.

---

## 7. System Architecture

```
+-------------------------------------------------------------+
|                    USER INTERFACE LAYER                     |
|  Browser Extension (MV3) . Web Workspace . Desktop Monitor  |
+---------------------------+---------------------------------+
                            | HTTPS / WSS
                            v
+-------------------------------------------------------------+
|                  API GATEWAY & SECURITY                     |
|  FastAPI . Token Auth . Sliding-Window Rate Limiting        |
|  SSRF Sanitizer . IP/Domain Whitelist Filter                |
+---------------------------+---------------------------------+
                            |
          +-----------------+-----------------+
          v                 v                 v
  +------------+   +------------+   +---------------------+
  | Normalizer |   |Verification|   |Evidence Provenance  |
  |& Extractor |   |Orchestrator|   |Ledger               |
  |            |   |            |   |                     |
  | entities   |   |Companies   |   |source snapshots     |
  | claims     |   |House (UK)  |   |authority rating     |
  | domains    |   |UAE NER     |   |independence ratio   |
  | contacts   |   |Domain WHOIS|   |user-verifiable path |
  +------+-----+   +------+-----+   +---------+-----------+
         +-----------------+------------------+
                           v
+-------------------------------------------------------------+
|                   CECT REASONING ENGINE                     |
|  Coherence (C)       -> Logical compatibility of claims     |
|  Evidence Indep. (E) -> Source independence from claimant   |
|  Consistency (C)     -> Identity & registry alignment       |
|  Trajectory (T)      -> Escalation & velocity tracking      |
+---------------------------+---------------------------------+
                            v
+-------------------------------------------------------------+
|                  RISK + CONFIDENCE ENGINE                   |
|  Multi-signal weighted synthesis . Signal reliability .     |
|  Confidence calibrated independently from risk level        |
+---------------------------+---------------------------------+
                            |
          +-----------------+-----------------+
          v                 v                 v
  +------------+   +------------+   +---------------------+
  |Explanation |   |Trust Graph |   |Meeting Shield &     |
  |Engine      |   |& Intel     |   |Media Auth           |
  |            |   |            |   |                     |
  |"Why it     |   |Entity nodes|   |Synthetic voice      |
  |matters"    |   |HMAC Domain |   |Face artifacts       |
  |Actionable  |   |threat cache|   |Deepfake alerts      |
  |next steps  |   |Anonymized  |   |Real-time meeting    |
  +------------+   +------------+   +---------------------+
                            |
                            v
+-------------------------------------------------------------+
|          CROSS-DOMAIN TRUST INTEGRITY LEDGER                |
|  Cryptographically hash-chained append-only audit trail     |
+-------------------------------------------------------------+
```

---

## 8. Verification Source Adapters

| Adapter | Registry | Country Coverage | Status |
|---|---|---|---|
| `CompaniesHouseAdapter` | UK Companies House (official API) | UK | Live + mock fallback |
| `SECEdgarAdapter` | US SEC EDGAR full-text search | US | Live + mock fallback |
| `IndiaMCAAdapter` | Ministry of Corporate Affairs | India | Live + mock fallback |
| `UAENERAdapter` | UAE National Economic Register | UAE / Gulf | Live + mock fallback |
| `OfficialWebsiteAdapter` | Domain WHOIS + DNS MX (RDAP) | Global | Live |

**Circuit Breaker policy:** If any adapter is offline or credentials are missing, it gracefully returns `SourceStatus.UNAVAILABLE` with `risk_boost = 0.0` — no false alarms (P1, P2).

---

## 9. ML Classifiers (Leakage-Aware, MEASURED)

All classifiers are lightweight scikit-learn models (TF-IDF + Linear SVM / Logistic Regression / HistGradientBoosting). Evaluation uses `StratifiedGroupKFold(5)` with near-duplicate clustering (cosine >= 0.90) or domain-grouped splits. Hyperparameters tuned on Fold 1 validation only; test Fold 0 scored once.

| Model | Task | Measured Test F1 | Real-World @ 5% Base Rate | Gate 1 |
|---|---|---|---|---|
| `job_scam_v2` | Binary job scam detection | 0.5931 [CI: 0.49–0.68] | Precision: 0.8959, FPR: 0.0027 | PASS |
| `sentinel_financial_fraud_v2` | Financial fraud OVR | 0.9080 [CI: 0.89–0.92] | Precision: 0.9897, FPR: 0.0005 | PASS |
| `sentinel_romance_sextortion_v2` | Romance extortion OVR | 1.0000 [CI: 1.00–1.00] | Precision: 1.0000, FPR: 0.0000 | PASS |
| `sentinel_government_impersonation_v2` | Govt impersonation OVR | 0.9145 [CI: 0.90–0.93] | Precision: 0.7245, FPR: 0.0180 | FAIL — Prec < 0.75 |
| `sentinel_bank_phishing_v2` | Bank phishing OVR | 0.9004 [CI: 0.88–0.92] | Precision: 0.6060, FPR: 0.0342 | FAIL — Prec < 0.75 |
| `url_char_ngram_v2` | URL phishing (char n-gram) | 0.9287 [CI: 0.92–0.94] | Precision: 0.3143, FPR: 0.1122 | FAIL — FPR > 0.05 |
| `url_tabular_v2` | URL phishing (70 lexical features) | 0.9421 [CI: 0.93–0.95] | Precision: 0.3455, FPR: 0.0987 | FAIL — FPR > 0.05 |

**Production gates:** FPR <= 0.05 AND Precision >= 0.75 at 5% base rate, required before rollout.

---

## 10. API Endpoints (Selected)

**Base URL:** `http://127.0.0.1:8000`

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | System health, version, uptime |
| `POST` | `/api/v1/verify` | Core job/offer verification pipeline |
| `POST` | `/api/v1/call-guard/invite/check` | Layer 0 — pre-call invite link SSRF-safe triage |
| `POST` | `/api/v1/meeting-shield/session/start` | Start live meeting inspection (explicit consent) |
| `POST` | `/api/v1/meeting-shield/session/audio-chunk` | Audio chunk — voice cloning detection |
| `POST` | `/api/v1/meeting-shield/session/video-chunk` | Video chunk — deepfake face-swap detection |
| `POST` | `/api/v1/meeting-shield/session/{id}/end` | End session, return aggregated safety verdict |
| `POST` | `/api/v1/threat-intelligence/report` | Submit anonymized community scam pattern |
| `GET` | `/api/v1/threat-intelligence/patterns` | List active threat patterns |
| `GET` | `/api/v1/ledger/audit-trail` | Export SHA-256 hash-chained audit blocks |
| `POST` | `/api/v1/recovery` | Phase 6 post-incident recovery automation |
| `POST` | `/api/v1/privacy-sandbox/consent` | Configure/revoke local baseline consent |
| `GET` | `/metrics` | Prometheus /metrics endpoint (Phase 8 SRE) |

Interactive Swagger docs at `http://127.0.0.1:8000/docs`.

---

## 11. Security Architecture

| Threat | Mitigation |
|---|---|
| SSRF | `SSRFShield` blocks RFC 1918 private IPs, loopback, link-local, and `169.254.169.254` cloud metadata |
| Credential leakage | API keys in `.env` only; `.env.example` checked in with placeholder values |
| Token auth | Bearer token on all non-public API routes |
| Rate limiting | Sliding-window rate limiter on API gateway |
| Data minimisation | Content script extracts only fields required for verification; zero raw telemetry |
| Differential Privacy | Local baseline: epsilon <= 1.0, min N >= 20 observations, gradient norm clipping |
| Audit ledger | SHA-256 hash-chained, append-only — tampering is cryptographically detectable |
| SBOM | CycloneDX v1.5 SBOM (`sbom-cyclonedx.json`) for supply-chain audit |

---

## 12. Tech Stack

| Layer | Technologies |
|---|---|
| **Browser Extension** | Chrome MV3, HTML5, Vanilla CSS3, JavaScript ES6+ |
| **Web Workspace UI** | HTML5 (single-page, 64 KB), Passport Control CSS Design System, Vanilla JS |
| **Desktop App** | Tauri (Rust shell), HTML/CSS/JS frontend, always-on-top floating HUD |
| **Backend API** | Python 3.14+, FastAPI, Pydantic v2, Uvicorn |
| **ML Engine** | Scikit-Learn 1.9+, Joblib, TF-IDF N-Grams, Linear SVM, Logistic Regression, HistGradientBoosting |
| **Database / ORM** | SQLite (`lifelens.db`), SQLAlchemy ORM (PostgreSQL-ready via env var) |
| **Security** | SSRFShield, CORS controls, Token auth, Audit event logger |
| **Observability** | Prometheus `/metrics`, alerting rules (`alerts.yml`), config (`prometheus.yml`) |
| **Containerisation** | Docker (`Dockerfile`), Docker Compose (`docker-compose.yml`) |
| **Infrastructure** | Terraform (`terraform/`), Kubernetes manifests (`kubernetes/`) |
| **CI / CD** | GitHub Actions (`.github/`), CVE gate, secret scanning, ONNX export, CycloneDX SBOM |
| **Testing** | Pytest — 287/287 passing across 27 suites |

---

## 13. Project Structure (Canonical)

```
Life_Lens_Ai/
├── apps/
│   ├── api/
│   │   └── app/
│   │       ├── api/            — FastAPI route handlers
│   │       ├── cect/           — CECT reasoning engine
│   │       ├── detectors/      — 7 specialised detectors
│   │       ├── explanations/   — Plain-language explanation generator
│   │       ├── integrations/   — Platform adapters (Zoom, Meet, Teams...)
│   │       ├── models/         — Canonical domain models
│   │       ├── repositories/   — DB models & CRUD
│   │       ├── risk/           — Risk & confidence engine
│   │       ├── schemas/        — Pydantic v2 schemas
│   │       ├── security/       — SSRF Shield
│   │       ├── services/       — Extractor, normalizer, trust graph
│   │       ├── verification/   — Source adapters (CH, SEC, MCA, NER, WHOIS)
│   │       └── main.py         — FastAPI entry point
│   ├── extension/              — Chrome MV3 extension
│   │   ├── manifest.json
│   │   └── src/
│   │       ├── background/     — Service worker
│   │       ├── content/        — DOM inspector (job boards)
│   │       ├── sidepanel/      — Primary result UI
│   │       ├── popup/          — Toolbar popup
│   │       ├── components/     — Shared UI components
│   │       ├── services/       — API client, extractors
│   │       └── types/          — Shared type definitions
│   ├── desktop/
│   │   ├── src/                — Floating HUD frontend
│   │   └── src-tauri/          — Rust Tauri shell
│   └── web/
│       ├── index.html          — Single-page Web Workspace (7 screens)
│       ├── styles.css          — Passport Control design system
│       └── app.js              — Verification UI & API integration
├── datasets/
│   ├── job_scam_text/          — DIFrauD + Sentinel corpora
│   ├── phishing_urls/          — PhishTank + CompPhish
│   ├── company_registry_reference/
│   └── evaluation/             — Benchmark metrics runner
├── models/
│   ├── job_scam_v2/
│   ├── sentinel_financial_fraud_v2/
│   ├── sentinel_government_impersonation_v2/
│   ├── sentinel_bank_phishing_v2/
│   ├── sentinel_romance_sextortion_v2/
│   ├── url_char_ngram_v2/
│   └── url_tabular_v2/
├── packages/
│   ├── schemas/                — Shared cross-surface type schemas
│   ├── scoring/                — Shared scoring utilities
│   ├── shared-types/
│   └── source-adapters/
├── scripts/
│   ├── predict.py              — Unified CLI inference (text & URL)
│   ├── dataset_quality_check.py
│   ├── train_baseline_model.py
│   └── train_phishing_url_model.py
├── tests/                      — 287 passing tests across 27 suites
├── docs/                       — Model cards, supplementary docs
├── infra/                      — Infrastructure configs
├── kubernetes/                 — K8s deployment manifests
├── terraform/                  — IaC for cloud provisioning
├── Dockerfile
├── docker-compose.yml
├── prometheus.yml
├── alerts.yml
├── sbom-cyclonedx.json
├── lifelens.db                 — SQLite database (local dev)
├── requirements.txt
├── pyproject.toml
├── .env.example                — Environment variable template
└── README.md
```

---

## 14. Implementation Phase Status

| Phase | Description | Status |
|---|---|---|
| Phase 1 | Core MVP: CECT engine, adapters, browser extension, web UI | Complete |
| Phase 2 | Cross-platform entity trust graph | Complete |
| Phase 3 | Community intel, 6-stage trust trajectory engine | Complete |
| Phase 4 | Live meeting shield (audio + video chunks) | Complete |
| Phase 5 | SHA-256 hash-chained unified trust integrity ledger | Complete |
| Phase 6 | Post-incident damage mitigation & recovery automation | Complete |
| Phase 7 | Multi-tenant enterprise API, scoped keys, HMAC webhooks, Python SDK | Complete |
| Phase 8 | Production SRE: Prometheus `/metrics`, auto-healing circuit breakers | Complete |
| Phase A | Honesty & hardening: mock zero-weight assertions, `[SIMULATED]` badges | Complete |
| Phase B | Call Guardian Layer 0: SSRF-safe invite link & typosquatting triage | Complete |
| Phase C | Desktop Call Guard: local trajectory engine, 7 triggers, out-of-band interstitial | Complete |
| Phase D | Platform integrations, Rule C shared-origin evidence independence | Complete |
| Phase E | Media forensics calibration: Rule B weight cap, ECE reliability curves | Complete |
| Phase F | Passport Control design system (Stitch UI, stamp verdicts) | Implemented |
| Phase G | 7 new specialised detectors: code scanner, digital arrest, voice clone, quishing | Complete |
| Phase H | Distribution: in-memory OCR, Telegram/WhatsApp bots, voice-note triage | Complete |
| Phase I | Response & impact: RDAP abuse takedown drafts, 3-screen Golden-Hour recovery | Complete |
| Phase J | Trust & governance: disputes + proof-of-control, calibration ECE, canaries | Complete |
| Phase K | Engineering hardening: ONNX v1.16 export, CycloneDX SBOM, CI CVE gate | Complete |
| Phase L | Pilot readiness: campus placement kit, migration corridor advisories, privacy analytics | Complete |

**Test count:** 287/287 passing (Baseline: 273 → Phase 1: 280 → Phase 4: 283 → Phase 7: 287)

---

## 15. Known Limitations & Open Production Gates


1. **Registry data fragmentation** — Every country's corporate registry differs in API access and data structure; some require scraping under rate-limit contracts.
2. **URL phishing model FPR** — Both URL classifiers fail Gate 1 (FPR > 0.05 at 5% base rate). Not gated for production. Require threshold re-tuning or stronger feature sets.
3. **Govt impersonation & bank phishing precision** — Sentinel OVR classifiers fail Gate 1 (Precision < 0.75 at 5% base rate). Not gated for production.
4. **Field validation pending** — The system is a **feature-complete prototype, not field-validated**. Prospective validation on candidate migration corridors requires live deployment approvals.
5. **Biometric layers are conceptual** — Deepfake detection (voice clone, facial synthesis) signals are defined in the data model and API schema, but no biometric models, raw audio recordings, or facial data are processed in this release.
6. **Asymmetric false-positive cost** — Wrongly flagging a legitimate company erodes trust; explanation-first design (evidence cards, not blind blocking) mitigates this by design.

---

*Document reflects repository state as at 2026-10-20.*
