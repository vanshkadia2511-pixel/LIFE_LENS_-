# LifeLens Ω — API Reference Manual

**API Version:** 2.0.0  
**Base URL:** `http://127.0.0.1:8000`  
**Implements:** Implementation Plan §91, §92  

---

## 1. System Health

### `GET /health`
Returns system status, service uptime, and operational version.

**Response:**
```json
{
  "status": "healthy",
  "service": "lifelens-omega-api",
  "version": "2.0.0",
  "timestamp": "2026-09-23T15:00:00Z"
}
```

---

## 2. Core Job & Offer Verification (Phase 1)

### `POST /api/v1/verify`
Runs the complete LifeLens Ω verification pipeline on a job posting or recruiter interaction.

**Request Body:**
```json
{
  "request_id": "req_uk_job_451",
  "job_title": "Senior Cloud Infrastructure Engineer",
  "company_name": "Acme Tech Solutions Ltd",
  "company_website": "https://www.acmetech.co.uk",
  "recruiter_name": "David Miller",
  "recruiter_email": "david.miller@acmetech.co.uk",
  "claimed_country": "GB",
  "job_description": "Exciting remote position. Apply via our official careers portal."
}
```

**Response:**
```json
{
  "request_id": "req_uk_job_451",
  "processed_at": "2026-09-23T15:01:00Z",
  "risk_assessment": {
    "risk_level": "LOW",
    "risk_score": 0.08,
    "confidence": 0.92,
    "primary_concerns": [
      "No critical risk patterns or unverified claims detected."
    ]
  },
  "cect_assessment": {
    "coherence_score": 0.95,
    "evidence_independence_score": 0.90,
    "consistency_score": 0.95,
    "trajectory_score": 0.90,
    "confidence": 0.92
  },
  "explanation": {
    "summary_headline": "VERIFIED: Key claims and company presence are well-supported.",
    "what_was_checked": ["Company Identity against official business registries"],
    "what_was_found": ["Verified: Company is officially registered in authoritative government registry."],
    "recommended_next_steps": ["Proceed with normal review and standard recruitment process."]
  }
}
```

---

## 3. Trust Graph & Community Threat Intel (Phase 2 & 3)

### `POST /api/v1/threat-intelligence/report`
Submits an anonymized community scam report (stores zero PII, domains stored as HMAC hashes).

**Request Body:**
```json
{
  "pattern_type": "UPFRONT_FEE",
  "geography": "GB",
  "domain": "fake-recruitment-agency.com"
}
```

### `GET /api/v1/threat-intelligence/patterns`
Lists all active community scam patterns and detection confidence levels.

---

## 4. Live Meeting Shield (Phase 4)

### `POST /api/v1/meeting-shield/session/start`
Initializes a live meeting inspection session with explicit user consent.

**Request Body:**
```json
{
  "meeting_title": "Technical Screening Interview",
  "platform": "Google Meet",
  "user_consent": true
}
```

### `POST /api/v1/meeting-shield/session/audio-chunk`
Inspects an audio stream chunk for synthetic voice synthesis / cloning.

**Request Body:**
```json
{
  "session_id": "shield_9f1a23bc8e01",
  "duration_ms": 1000,
  "spectral_flatness": 0.85,
  "pitch_variance": 0.02,
  "synthetic_voice_prob": 0.92
}
```

### `POST /api/v1/meeting-shield/session/video-chunk`
Inspects a video stream chunk for deepfake face-swap or lip desynchronization.

### `POST /api/v1/meeting-shield/session/{session_id}/end`
Ends the session and delivers an aggregated safety verdict.

---

## 5. Unified Trust Platform & Cryptographic Ledger (Phase 5)

### `POST /api/v1/unified/verify`
Executes the holistic 10-step LifeLens Ω Mental Model (§101) across all multi-modal signals and records the verdict into the cryptographic Trust Integrity Ledger.

### `GET /api/v1/ledger/audit-trail`
Exports the SHA-256 hash-chained verification audit blocks with cryptographic proof of chain integrity.

### `POST /api/v1/privacy-sandbox/consent`
Configures or revokes user consent for local baseline feature processing (§97, §98).

### `POST /api/v1/privacy-sandbox/reset/{user_id}`
Triggers an immediate, zero-knowledge purge of all local observation buffers and privacy budget consumption counters.
