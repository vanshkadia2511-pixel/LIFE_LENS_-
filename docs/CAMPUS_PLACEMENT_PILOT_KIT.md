# LifeLens Ω — Campus Placement-Cell Pilot Kit

> **Document Type:** Operational Pilot Protocol & Guidance  
> **Target Audience:** University Placement Officers, Student Career Cells, Student Participants  
> **Status:** Draft / Ready for Institutional Review Board (IRB) Review  
> **Classification:** Non-Biometric, Privacy-Preserving Career Safeguard  

---

## 1. One-Page Explainer for Students and Placement Officers

### What is LifeLens Ω?
LifeLens Ω is an explainable offer verification and reality integrity system designed to protect students and recent graduates from employment scams, fake recruitment letters, advance-fee training rackets, and digital-arrest impersonation during campus placements and job searches.

### Core Principles
1. **P1 — Verification over Accusation:** We never label any person or company as a "scammer" or "fake". We inspect factual inconsistencies in offers, domains, registration records, and financial requests.
2. **P2 — Signal is Not Proof:** An anomaly (e.g. a new domain or free webmail host) is an invitation to double-check independently, not definitive proof of malice.
3. **P5 — Privacy by Default:** No passwords, bank account numbers, audio recordings, or biometric identifiers are ever stored.
4. **P6 — Human-in-the-Loop:** LifeLens Ω provides verification checklists and out-of-band callback recommendations. The student and placement officer make all final decisions.

### What LifeLens Ω Does
- Inspects recruiter email domains against authentic company SPF/DKIM/DMARC records.
- Verifies whether an offer demands advance security deposits, laptop fees, or courier charges (a universal red flag prohibited by labor law).
- Flags high-risk patterns such as interviews conducted entirely on unsecured personal messaging apps (Telegram, WhatsApp) without official enterprise coordination.
- Equips the student with a step-by-step out-of-band verification guide (e.g., calling the listed corporate switchboard via official directory).

### What LifeLens Ω NEVER Does
- **Never labels a human being:** In adherence to Rule A, the system never outputs "fake person", "real recruiter", or "scammer". Permitted outputs are strictly: *"Needs Verification"*, *"Not independently verified"*, *"Verification step completed"*, or *"Request looks high-risk"*.
- **Never collects biometric data:** Voice, face recognition, or webcam video are strictly excluded (Rule D).
- **Never reports students to recruiters or campus disciplinary authorities.**

---

## 2. Participant Consent Form Template

```text
================================================================================
LIFELENS Ω CAMPUS RECRUITMENT VERIFICATION PILOT
INFORMED CONSENT & PRIVACY AGREEMENT
================================================================================

1. PURPOSE OF THE PILOT
You are invited to participate in a research pilot evaluating the usability and
efficacy of LifeLens Ω in identifying high-risk recruitment communications.

2. VOLUNTARY PARTICIPATION
Participation is 100% voluntary. Declining to participate or withdrawing at any
point will NOT affect your academic standing, placement cell registration,
or job eligibility in any way.

3. DATA PROTECTION & PRIVACY COMMITMENTS
- ZERO CONTENT RETENTION: Offer letter text and emails submitted for verification
  are processed in-memory. They are NEVER stored on disk or shared with third parties.
- ZERO BIOMETRIC COLLECTION: No audio, video, facial, or biometric data is collected.
- PSEUDONYMOUS TELEMETRY: System metrics use irreversibly salted HMAC session
  tokens (session_salt rotates daily). Your name, email, and IP address are never logged.

4. USER RIGHTS
- You may withdraw your consent at any time without penalty.
- You have the right to request a complete summary of pilot findings upon conclusion.

STUDENT ACKNOWLEDGMENT:
[ ] I confirm that I am 18 years of age or older.
[ ] I have read and understood the explanation above.
[ ] I consent to testing the LifeLens verification assistant during my placement search.

Participant Signature / Digital Token: ___________________________ Date: ____________
```

---

## 3. Post-Verification Student Feedback Survey

Administered anonymously via a 5-point Likert scale (1 = Strongly Disagree, 5 = Strongly Agree):

1. **Comprehension & Clarity:**
   - *"The verification explanation clearly highlighted which specific facts were inconsistent or unverified."* [1 / 2 / 3 / 4 / 5]
2. **Actionability:**
   - *"The out-of-band callback checklist gave me clear, practical steps to verify the recruiter directly."* [1 / 2 / 3 / 4 / 5]
3. **Tone & Objectivity:**
   - *"The system maintained an objective, factual tone without making unsubstantiated accusations against individuals."* [1 / 2 / 3 / 4 / 5]
4. **False Alarm Reporting:**
   - *"Did you feel the system flagged a legitimate campus employer unnecessarily? If yes, please specify employer industry without sharing personal details."* [Yes / No / Comments]
5. **Psychological Safety:**
   - *"The presence of the verification shield reduced my anxiety about fraudulent job offers."* [1 / 2 / 3 / 4 / 5]

---

## 4. Institutional Ethics & Safety Checklist

- [x] **No Grade or Placement Disadvantage:** Participation status is strictly inaccessible to recruiting companies or academic evaluators.
- [x] **Zero Persistent Media Storage:** Asserted in automated test suites; any image or audio input is processed in memory and discarded immediately.
- [x] **No Commercial Data Monetization:** Pilot data is used strictly for safety calibration and academic evaluation.
- [x] **Independent Recourse:** If a student suspects a scam, the placement cell provides immediate access to designated campus career counselors and legal aid resources.
- [x] **Accessible Design:** Meets WCAG 2.1 AA accessibility standards with screen-reader friendly high-contrast design.

---

## 5. Metrics Plan

| Metric Name | Type | Target | Measurement Method |
| :--- | :--- | :--- | :--- |
| **Comprehension Rate** | TARGET | >= 85.0% | Post-verification survey score >= 4/5 on question 1. |
| **Checklist Action Rate** | TARGET | >= 70.0% | Telemetry count of students completing at least 1 out-of-band verification action before signing or paying. |
| **False Alarm Rate** | TARGET | <= 5.0% | Percentage of disputed findings on approved on-campus recruiters. |
| **Review Latency** | TARGET | <= 3.0 s | End-to-end time from invite/offer upload to interactive checklist generation. |
| **Zero Raw Storage Violations** | MEASURED | 0 violations | Continuous automated assertion in CI security test harness. |
