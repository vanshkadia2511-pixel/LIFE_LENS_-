# LifeLens Ω — Threat Model

> **Version**: 1.0.0  
> **Last Updated**: 2026-09-23  
> **Classification**: Internal Engineering

---

## 1. Overview

LifeLens Ω is a privacy-aware AI trust-verification system that analyzes claims, evidence, identity, consistency, and interaction trajectories to help people verify high-impact digital interactions before they trust, pay, share, or act.

This document captures the threat model: the assets we protect, the adversaries we face, the attacks we mitigate, and the residual risks we accept.

---

## 2. Assets

| Asset | Description | Sensitivity |
|-------|-------------|-------------|
| User verification requests | Job/recruiter details submitted for analysis | HIGH |
| User feedback | Outcome labels submitted after interaction | MEDIUM |
| Audit logs | Record of all verification events | HIGH |
| Verification source credentials | API keys for Companies House, SEC, MCA, etc. | CRITICAL |
| Community threat patterns | Aggregated scam intelligence | MEDIUM |
| Extension code | JavaScript running in browser context | HIGH |

---

## 3. Threat Actors

| Actor | Capability | Motivation |
|-------|-----------|------------|
| **Recruitment scammers** | Low–Medium technical | Financial gain via job-offer fraud |
| **Data harvesters** | Medium | Collect PII from users |
| **Nation-state actors** | High | Disrupt anti-fraud infrastructure |
| **Malicious extension developers** | Medium | Hijack browser permissions |
| **API abusers** | Low–Medium | Rate-limit bypass, scraping |
| **Internal threat** | High (access) | Misuse of audit data |

---

## 4. Attack Vectors

### 4.1 Server-Side Request Forgery (SSRF)
**Mitigated by**: `apps/api/app/security/ssrf.py`  
- All outbound URLs are validated against an allowlist of approved verification sources.
- Private IP ranges, cloud metadata endpoints (169.254.169.254), and loopback addresses are blocked.
- Redirects are not followed blindly.

### 4.2 Prompt/Input Injection
**Mitigated by**:
- Pydantic input validation on all API payloads.
- Claim extraction uses structured rules, not raw LLM completions.
- No user content is injected into SQL queries (ORM-only).

### 4.3 Data Exfiltration via Verification Requests
**Mitigated by**:
- Minimal data collection principle: only fields required for verification.
- No raw job descriptions or message content are stored.
- Audit logs are stripped of passwords, tokens, and unnecessary PII.

### 4.4 Extension Permission Abuse
**Mitigated by**:
- Manifest V3 with declarative permissions (no broad host permissions).
- Content Security Policy headers.
- Background service worker instead of persistent background page.
- Minimal host permissions: only supported job sites.

### 4.5 API Rate Limit Bypass / Abuse
**Mitigated by**:
- Rate limiting middleware on all public endpoints.
- Request validation with strict field types.
- Monitoring alerts on anomalous request volumes.

### 4.6 Supply Chain Attacks
**Mitigated by**:
- `requirements.txt` with pinned dependency versions.
- Dependency scanning in CI pipeline.
- No dynamic code evaluation.

### 4.7 Community Pattern Poisoning
**Risk**: Adversaries submit false reports to downgrade legitimate companies.  
**Mitigated by**:
- Pattern confidence requires minimum report counts.
- Domain hashing prevents targeted poisoning (cannot know which hash to target).
- Human review required before HIGH-confidence elevation.

---

## 5. STRIDE Analysis

| Threat | Example | Mitigation |
|--------|---------|------------|
| **Spoofing** | Fake API credentials | HMAC signing, secret rotation |
| **Tampering** | Modify verification result in transit | HTTPS-only, response integrity |
| **Repudiation** | Deny sending a verification | Immutable audit log with timestamps |
| **Information Disclosure** | Leak user job data | Minimal collection, no raw PII in logs |
| **Denial of Service** | Flood verification endpoint | Rate limiting, timeout guards |
| **Elevation of Privilege** | Admin endpoint access | Kill-switch endpoints require internal access |

---

## 6. Residual Risks

| Risk | Likelihood | Impact | Accepted |
|------|-----------|--------|----------|
| Verification source outage causing false negatives | MEDIUM | HIGH | Yes — `UNAVAILABLE` state prevents silent failure |
| Community pattern confidence miscalibration | LOW | MEDIUM | Yes — human review gate before HIGH elevation |
| Extension CSP bypass via browser 0-day | LOW | HIGH | Yes — defense in depth via background isolation |
| AI-generated fake company registrations fooling adapters | MEDIUM | HIGH | Deferred — Phase 3 research direction |

---

## 7. Security Requirements (§36)

- [ ] All API traffic over HTTPS in production
- [x] SSRF protection on all outbound verification calls
- [x] Pydantic input validation on all endpoints
- [x] Audit logging (who/what/when/which adapter/which result)
- [x] No passwords, tokens, or unnecessary PII in logs
- [ ] Secret management via environment variables / vault (not hardcoded)
- [x] Rate limiting on public verification endpoint
- [x] Kill switches for all adapters, rules, and features
- [ ] Dependency vulnerability scanning in CI

---

## 8. Extension Security (§37)

- Manifest V3 declarative net request only
- No `eval()` or dynamic code execution
- Content scripts scoped to supported job domains only
- All communication to API uses authenticated HTTPS
- Local state only for non-sensitive UI preferences
