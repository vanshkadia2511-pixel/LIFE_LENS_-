# LifeLens Ω — Privacy Architecture & Data Governance

**Document Version:** 2.0  
**Implements:** Implementation Plan §3 (P5), §77, §78, §79, §80, §92, §97, §98  

---

## 1. Privacy Principles (P5 — Privacy by Default)

LifeLens Ω is designed with strict data minimization:
1. **No Universal Monitoring:** LifeLens Ω does **not** record, intercept, or log unprompted private chats, keystrokes, or screen contents.
2. **Explicit User Consent:** Any meeting stream inspection or behavioral baseline recording requires opt-in consent (§80, §98).
3. **Local-First Processing:** Claim extraction and DOM parsing occur locally inside the browser extension before sending minimal structured metadata to the verification backend.

---

## 2. Data Governance Matrix (§78)

| Data Element | Stored On Server? | Retention Policy | Purpose |
|--------------|-------------------|------------------|---------|
| **Job Title & Description** | Transient (in-memory) | Session only | Claim extraction & CECT reasoning |
| **Recruiter Email & Domain** | Anonymized HMAC hash | 30 days (Threat Intel) | Pattern matching without exposing PII |
| **Registry Evidence Snapshots** | Cached (hashed key) | 24 hours | Adapter query deduplication & cache |
| **User Feedback** | Anonymized verdict | Permanent (Evaluation) | Benchmark precision & recall tracking |
| **Meeting Audio/Video Frames** | **NEVER STORED** | Immediate discard | In-memory synthetic anomaly scoring only |

---

## 3. Privacy Gates & Local Learning (§97, §98)

The system incorporates the **Federated Privacy Sandbox**:
- **Zero-Consent Lockout:** If `user_consent=False`, all analysis immediately aborts.
- **Differential Privacy Budgeting:** An $(\epsilon, \delta)$ privacy budget is tracked per device ($\epsilon \le 1.0$).
- **Instant Data Purge:** Users can call `POST /api/v1/privacy-sandbox/reset/{user_id}` at any time to purge all local observation buffers and reset all privacy consumption metrics.
