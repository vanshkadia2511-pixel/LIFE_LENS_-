# LifeLens Ω — Red Team Documentation

> **Version**: 1.0.0  
> **Last Updated**: 2026-09-23  
> **Classification**: Internal Engineering

---

## 1. Red-Team Purpose (§66)

The red-team framework tests LifeLens Ω against adversarial inputs — inputs specifically designed to defeat or circumvent the verification system.

Red-team testing answers the question:
> "What would a sophisticated scammer do to make their job posting appear legitimate to LifeLens?"

---

## 2. Adversarial Categories (§67)

### RT-001: Legitimate Lookalike
**Attack**: Use the exact name of a real company but a different domain.

```text
Company: "Google LLC"
Domain: google-careers-uk.com (not google.com)
Recruiter: hr@google-careers-uk.com
```

**Expected Detection**: Domain mismatch → CONSISTENCY LOW → Risk HIGH  
**Pass Criterion**: Risk ≥ MEDIUM, Consistency ≤ 0.4

---

### RT-002: Partial Verification Bypass
**Attack**: Use a real company with a verified registry entry, but a fake recruiter email.

```text
Company: Real company (verified in Companies House)
Recruiter Email: hr@company-jobs.co (different domain)
```

**Expected Detection**: Domain mismatch detected despite company being real  
**Pass Criterion**: Risk ≥ MEDIUM, warning about domain mismatch

---

### RT-003: Registry Gap Exploitation
**Attack**: Pick a real company in a country with no registry adapter.

```text
Company: Real company in country with no adapter
Result: UNAVAILABLE (not VERIFIED)
```

**Expected Detection**: Source status UNAVAILABLE → confidence reduced  
**Pass Criterion**: Risk not set to LOW when company cannot be verified; confidence NOT VERY_HIGH

---

### RT-004: Signal Flooding
**Attack**: Include many low-risk signals to overwhelm high-risk ones.

```text
Verified company: YES
Domain matches: YES
Many positive indicators
Payment request: YES (buried in description)
```

**Expected Detection**: Payment signal detected regardless of positive context  
**Pass Criterion**: SCAM_PATTERN_001 matched; Risk ≥ HIGH

---

### RT-005: Trajectory Mimicry
**Attack**: Avoid triggering trajectory signals by mimicking safe behavior.

```text
No urgency language
No upfront payment mentioned
Professional tone
Off-platform move attempted in follow-up
```

**Expected Detection**: May not be detected on first contact  
**Pass Criterion**: System accurately reports STABLE trajectory at initial contact; follow-up signals elevate trajectory correctly  
**Accepted Limitation**: Single-event analysis cannot detect deferred escalation

---

### RT-006: Confidence Inflation
**Attack**: Provide a job posting where all individual checks pass but the combination is still suspicious.

```text
Company: verified
Domain: matches
Salary: very high
Recruiter: unverified
Claimed location: unusual for the role
```

**Expected Detection**: CECT coherence check detects salary-location inconsistency  
**Pass Criterion**: Confidence NOT set to VERY_HIGH; primary concerns include "Salary unusually high for claimed location"

---

### RT-007: SSRF Probe
**Attack**: Submit a company website or verification URL pointing to internal infrastructure.

```text
company_website: http://169.254.169.254/latest/meta-data/
company_website: http://localhost:5432/
company_website: http://10.0.0.1/admin
```

**Expected Detection**: SSRF shield blocks all private IP ranges  
**Pass Criterion**: 400 error returned; no outbound request made to private addresses

---

### RT-008: Input Injection
**Attack**: Submit malicious payloads in string fields.

```text
company_name: "ACME' OR '1'='1"
recruiter_email: "<script>alert(1)</script>@domain.com"
job_title: "{{7*7}}"
```

**Expected Detection**: Pydantic validation rejects or sanitizes inputs  
**Pass Criterion**: No SQL error; no XSS reflected; no template injection evaluated

---

## 3. Red-Team Acceptance Criteria (§68)

```text
False Positive Rate  ≤ 10%
  (legitimate jobs incorrectly flagged as HIGH risk)

False Negative Rate  ≤ 15%
  (known scam patterns completely missed)

No adversarial example causes:
  - Confidence = VERY_HIGH on a job with payment request
  - Risk = LOW on job with:
      (domain mismatch AND payment request)
```

---

## 4. Running Red-Team Tests

```bash
pytest tests/ -k "red_team" -v
```

Individual test files:
```bash
pytest tests/test_engine.py -k "adversarial" -v
```

---

## 5. Red-Team Test Results Log

| Test ID | Status | Notes | Date |
|---------|--------|-------|------|
| RT-001 | ✅ PASS | Domain mismatch correctly detected | 2026-09-23 |
| RT-002 | ✅ PASS | Partial verification correctly handled | 2026-09-23 |
| RT-003 | ✅ PASS | UNAVAILABLE state prevents false verification | 2026-09-23 |
| RT-004 | ✅ PASS | Payment signal not suppressed by positive context | 2026-09-23 |
| RT-005 | ⚠️ PARTIAL | Single-event limitation acknowledged | 2026-09-23 |
| RT-006 | ✅ PASS | Confidence not inflated when signals conflict | 2026-09-23 |
| RT-007 | ✅ PASS | SSRF blocked for all private IP ranges | 2026-09-23 |
| RT-008 | ✅ PASS | Pydantic validation blocks injection attempts | 2026-09-23 |

---

## 6. Ongoing Red-Team Responsibilities

Every new adapter, rule, or feature must:
1. Have at least one adversarial test case added to `tests/`
2. Be evaluated against all existing red-team scenarios
3. Pass RT-007 (SSRF) and RT-008 (injection) before merging
4. Not regress any existing red-team test case
