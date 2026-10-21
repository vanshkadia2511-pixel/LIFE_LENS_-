# LifeLens Ω — Privacy Documentation

> **Version**: 1.0.0  
> **Last Updated**: 2026-09-23  
> **Classification**: Internal Engineering

---

## 1. Privacy Principles (§33)

LifeLens Ω is built on **local-first, user-controlled** privacy:

1. **Minimal data collection** — collect only what is strictly required for verification.
2. **No surveillance** — the system does not continuously monitor private communications.
3. **No behavioral profiling** — the system does not build persistent behavioral profiles without explicit consent.
4. **User control** — the user decides what to verify and when.
5. **Transparency** — the user sees exactly what was checked and what the system found.
6. **No raw message content stored** — only structured, minimal fields required for verification.

---

## 2. Data Classes (§34)

| Class | Description | Examples | Retention |
|-------|-------------|---------|-----------|
| **CLASS_1_MINIMAL** | Minimum needed for verification | Company name, job title, domain | Session only (not persisted) |
| **CLASS_2_STRUCTURED** | Structured entity data | Recruiter email, phone (normalized) | 90 days max |
| **CLASS_3_DERIVED** | Derived, non-identifying signals | Risk level, CECT scores | 1 year (anonymized) |
| **CLASS_4_AUDIT** | Audit event metadata | Who/what/when (no raw content) | 2 years |
| **CLASS_5_COMMUNITY** | Anonymized pattern data | Hashed domains, scam pattern counts | Indefinite (no PII) |

---

## 3. Consent Model (§35)

Every verification request requires:

```
consent_for_analysis: bool = True
```

If `consent_for_analysis = False`, the request is rejected.

**Phase 2 behavioral baselines** (§98) require additional explicit consent:
- Explicit opt-in (separate from general consent)
- Minimum sample size before activation
- User can reset or delete their baseline at any time

---

## 4. What Is NOT Collected

The following are explicitly prohibited by architecture:

- Raw email body content
- Chat message transcripts
- Video call recordings
- Continuous screen monitoring data
- Authentication tokens or passwords
- Unnecessary full message content
- Private social media data without explicit permission

---

## 5. Domain Hashing (§82)

Community threat intelligence stores domains as **HMAC-SHA256 hashes**, not raw domain strings.

- One-way transform: the original domain cannot be recovered from the hash.
- Salt is environment-specific and never exposed in API responses.
- Public pattern reports never include domain values or hashes.

---

## 6. Audit Log Privacy (§72)

Audit logs record:
- `who` — an anonymized session identifier (not user PII)
- `what` — the type of verification action
- `when` — timestamp
- `which source/adapter/version/result` — technical metadata

Audit logs **never** contain:
- Passwords
- Private authentication tokens
- Raw job description content
- Sensitive personal information

---

## 7. Extension Privacy

The browser extension:
- Does NOT send full page content to the API
- Extracts only the specific fields required for verification (company name, domain, job title, recruiter contact)
- Does NOT monitor browsing history outside verification actions
- Local UI state (user preferences) is stored in `chrome.storage.local` only

---

## 8. Data Retention Schedule

| Data Type | Retention |
|-----------|-----------|
| Verification request payload | 90 days |
| Verification result (non-PII) | 1 year |
| Audit events | 2 years |
| User feedback | 1 year |
| Community patterns (anonymized) | Indefinite |
| Raw credentials/tokens | Not stored |

---

## 9. User Rights

Users have the right to:
- Know what data was collected during their verification session
- Request deletion of their verification history
- Opt out of community threat pattern contribution
- Reset any behavioral baseline (Phase 2 feature)

---

## 10. Privacy Review Gate (Gate 2 — MVP → Pilot)

Before moving to pilot, a privacy review must confirm:
- [ ] Minimal collection principle verified in code
- [ ] No PII in audit logs (verified by automated scan)
- [ ] Consent gates enforced at API level
- [ ] Retention policies implemented in database
- [ ] Extension permissions audited
- [ ] Community pattern system verified as PII-free
