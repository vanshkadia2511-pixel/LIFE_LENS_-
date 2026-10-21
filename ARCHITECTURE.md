# LifeLens Ω — System Architecture

**Document Version:** 2.0  
**Status:** Canonical Reference Architecture  
**Implements:** Implementation Plan §6, §7, §100, §101  

---

## 1. High-Level Architecture Overview

LifeLens Ω is a privacy-aware, multi-modal reality integrity and trust verification system. Rather than attempting a naive binary classification ("SCAM / SAFE"), LifeLens Ω grounds every finding in an auditable **Entity → Claim → Evidence** ledger evaluated through the 4-pillar **CECT Reasoning Framework** (Coherence, Evidence Independence, Consistency, Trajectory).

```text
┌───────────────────────────────────────────────────────────┐
│                 USER INTERFACE LAYER                      │
│ Browser Extension (MV3) · Web Workspace · Desktop Monitor │
└──────────────────────────┬────────────────────────────────┘
                           │ HTTPS / WSS
                           ▼
┌───────────────────────────────────────────────────────────┐
│                 API GATEWAY & SECURITY                    │
│ FastAPI · Token Auth · Sliding Window Rate Limiting ·     │
│ SSRF Sanitizer · IP/Domain Whitelist Filter               │
└──────────────────────────┬────────────────────────────────┘
                           │
      ┌────────────────────┼────────────────────┐
      ▼                    ▼                    ▼
┌──────────────┐   ┌──────────────┐   ┌─────────────────────┐
│ Normalizer   │   │ Verification │   │ Evidence Provenance │
│ & Extractor  │   │ Orchestrator │   │ Ledger (§13)        │
│              │   │              │   │                     │
│ entities     │   │ Companies    │   │ source snapshots    │
│ claims       │   │ House (UK)   │   │ authority rating    │
│ domains      │   │ UAE NER      │   │ independence ratio  │
│ contacts     │   │ Domain WHOIS │   │ user-verifiable path│
└──────┬───────┘   └──────┬───────┘   └──────────┬──────────┘
       │                  │                      │
       └──────────────────┼──────────────────────┘
                          ▼
┌───────────────────────────────────────────────────────────┐
│                  CECT REASONING ENGINE                    │
│                                                           │
│  Coherence (C)       → Logical compatibility of claims    │
│  Evidence Indep. (E) → Source independence from claimant  │
│  Consistency (C)     → Identity & registry alignment      │
│  Trajectory (T)      → Escalation & velocity tracking     │
└─────────────────────────┬─────────────────────────────────┘
                          ▼
┌───────────────────────────────────────────────────────────┐
│                 RISK + CONFIDENCE ENGINE                  │
│                                                           │
│  Multi-signal weighted synthesis · Signal reliability ·   │
│  Confidence calibrated independently from risk level      │
└─────────────────────────┬─────────────────────────────────┘
                          │
      ┌───────────────────┼───────────────────┐
      ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌─────────────────────┐
│ Explanation  │   │ Trust Graph  │   │ Meeting Shield &    │
│ Engine (§21) │   │ & Intel (§81)│   │ Media Auth (§99)    │
│              │   │              │   │                     │
│ "Why it      │   │ Entity nodes │   │ Synthetic voice     │
│ matters"     │   │ HMAC Domain  │   │ Face artifacts      │
│ Actionable   │   │ threat cache │   │ Deepfake alerts     │
│ next steps   │   │ Anonymized   │   │ Real-time meeting   │
└──────┬───────┘   └──────┬───────┘   └──────────┬──────────┘
       │                  │                      │
       └──────────────────┼──────────────────────┘
                          ▼
┌───────────────────────────────────────────────────────────┐
│         CROSS-DOMAIN TRUST INTEGRITY LEDGER               │
│ Cryptographically hash-chained append-only audit trail    │
└───────────────────────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### 2.1 Browser Extension (Manifest V3)
- **Content Script:** Inspects DOM of supported job boards (LinkedIn, Indeed, Reed, Glassdoor) and extracts structured employer claims.
- **Privacy Sandbox:** Only extracts fields necessary for verification (Company, Recruiter, Website, Description).
- **UI:** Transparently displays the Risk Badge, CECT Breakdown, Evidence Provenance Cards, and recommended independent verification actions.

### 2.2 Extraction & Normalization Layer
- Entity Normalizer: Strips legal entity suffixes (`Ltd`, `LLC`, `GmbH`), canonicalizes domains, and resolves aliases.
- Claim Extractor: Categorizes submitted claims into `IDENTITY`, `EMPLOYMENT`, `SALARY`, `VISA`, `PAYMENT`, `DOCUMENT`, `URGENCY`, and `CONTACT`.

### 2.3 Verification Orchestrator & Source Adapters
- `CompaniesHouseAdapter`: Authoritative UK public registry integration with live lookup and mock fallback.
- `UAENERAdapter`: Official UAE National Economic Register scraper/lookup for Gulf employment verification.
- `OfficialWebsiteAdapter`: Extracts and matches company domain names and DNS MX/WHOIS provenance records.
- `Circuit Breaker & Fallback Policy`: If any adapter is offline or missing credentials, it gracefully returns `SourceStatus.UNAVAILABLE` with `risk_boost=0.0` to avoid false alarms (P1, P2).

### 2.4 CECT Reasoning Engine (§14, §15)
- **Coherence (C):** Checks logical compatibility between claims (e.g. claimed location vs registered offices).
- **Evidence Independence (E):** Penalizes recruiter-provided collateral while weighting authoritative public sources.
- **Consistency (C):** Compares recruiter domains with registered corporate domains.
- **Trajectory (T):** Detects psychological pressure, urgency acceleration, off-platform migration, and monetary demands.

### 2.5 Real-Time Meeting Shield (§94 Phase 4, §99)
- Streaming frame/chunk inspector for video and audio meetings.
- Detects voice cloning markers (spectral flatness, pitch variance anomalies) and visual face-swap / reenactment boundaries.
- Dispatches instantaneous alerts with actionable verification questions for the user.

### 2.6 Cryptographic Trust Integrity Ledger (§100, §101 Phase 5)
- SHA-256 hash-chained block storage guaranteeing zero-tampering for past verification audit logs.
- Proof of verification exportable for enterprise and regulatory compliance.

### 2.7 Federated Privacy Sandbox (§97, §98)
- Zero-telemetry local learning gatekeeper.
- Enforces strict user consent verification, minimum observation thresholds ($N \ge 20$), Differential Privacy budget caps ($\epsilon \le 1.0$), and outlier gradient norm clipping.
