# LifeLens Ω — Data Retention & Lifecycle Policy

**Document Version:** 1.0  
**Effective Date:** 2026-10-12  
**Status:** Active Engineering Baseline  
**Scope:** All LifeLens Ω services, browser extensions, desktop agents, and API endpoints.

---

## 1. Core Principles (P5 & Rule D)

1. **Privacy by Default (P5):** Data collection is strictly minimized to what is necessary for verifiable claim assessment.
2. **Zero Media Persistence (Rule D):** Raw audio, video frames, webcam captures, and screenshots are **NEVER** persisted to disk, relational databases, or object storage. All processing occurs in volatile memory and buffers are discarded immediately upon signal extraction.
3. **Local-First Architecture:** Media forensics and client-side link checks execute on the user's endpoint. Only non-biometric, structured signals may be transmitted, and only with explicit user opt-in.

---

## 2. Retention Schedules by Data Classification

| Data Category | Retention Period | Storage Medium | Deletion / Discard Mechanism |
| :--- | :--- | :--- | :--- |
| **Raw Audio / Video Chunks** | **0 seconds (Immediate Discard)** | Volatile RAM only | Garbage collected immediately after frame FFT / feature extraction. |
| **Biometric Signatures & Templates** | **0 seconds (None Stored)** | None | Not captured or persisted. Rule D default: not built. |
| **Job Text / Recruiter Messages** | **Session Lifetime (Max 60 min)** | In-memory cache / ephemeral Redis | TTL expiration; purged on session end or manual clear. |
| **Verification Evidence Ledger** | **30 Days (Public Metadata Only)** | Append-only Cryptographic Ledger | Hash-anchored blocks retain salted entity metadata only; no victim PII. |
| **Community Threat Intelligence** | **Rolling 90 Days** | Key-value database | Salted HMAC domain hashes retained for pattern clustering; victim IDs purged. |
| **Recovery Incident Packets** | **0 seconds (Client-side Export)** | In-memory during export session | Downloaded directly as `.txt`/`.json`; never stored in backend database. |
| **SRE Health & Telemetry Metrics** | **14 Days** | Prometheus / Time-Series DB | Aggregated latency, error counts, and circuit breaker states; zero payload text. |

---

## 3. Ephemeral In-Memory Media Pipeline Safeguards

To prevent accidental data persistence:
1. Automated CI tests (`tests/test_in_memory_only.py`) verify that file handles are never opened for audio/video stream bytes.
2. Temporary upload directories (`/tmp`, `scratch/`, OS temp) are denied write permissions by backend media ingest services.
3. Database schemas strictly omit binary large object (`BLOB` / `BYTEA`) columns for media streams.

---

## 4. User Deletion & Erasure Protocol (GDPR Art. 17 / DPDP Act §12)

- **Browser Extension:** Clicking "Clear History" in the extension popup immediately purges Chrome local storage, session storage, and cached claims.
- **API Cache Purge:** Sending a `DELETE /api/v1/session/{session_id}` request immediately purges the session and associated evidence cards from the server's in-memory assessment store.
- **Cryptographic Anonymity:** Since the Trust Integrity Ledger stores only keyed HMAC hashes of public corporate registration numbers and SHA-256 state hashes, no personally identifiable information (PII) is permanently immured in the ledger.
