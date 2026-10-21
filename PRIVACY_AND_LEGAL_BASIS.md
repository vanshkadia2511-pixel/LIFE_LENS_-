# LifeLens Ω — Privacy & Legal Basis Assessment

> **DISCLAIMER:**  
> **STATUS: NEEDS LEGAL REVIEW**  
> This document represents an engineering and architectural privacy analysis. It does NOT constitute formal legal advice. A qualified privacy attorney must review this document prior to any production deployment or pilot across regulated jurisdictions.

---

## 1. Overview & Regulatory Scope

LifeLens Ω provides automated claim verification, public registry lookups, and multi-modal meeting protection against recruitment extortion and identity fraud. Because the system interacts with recruiter contact details, job postings, and streaming communication metadata, it is architected under strict international data privacy baselines:

1. **European Union:** General Data Protection Regulation (GDPR / Regulation (EU) 2016/679)
2. **India:** Digital Personal Data Protection Act, 2023 (DPDP Act 2023)
3. **United States (State Biometric Acts):** Illinois BIPA (740 ILCS 14/), Texas CUBI (Tex. Bus. & Com. Code § 503.001), California CCPA/CPRA

---

## 2. GDPR Legal Basis Analysis (EU / UK)

### 2.1 Standard Personal Data (Article 6)
- **User-Initiated Verifications (Article 6(1)(a) — Consent):**  
  When a candidate pastes a job description or launches the browser extension on a job board, verification proceeds under explicit, freely given user consent.
- **Fraud Prevention & Security (Article 6(1)(f) — Legitimate Interests):**  
  Processing publicly available corporate registry data (UK Companies House, SEC EDGAR) and comparing claimed domain names serves the legitimate interest of protecting users from advance-fee fraud, illegal trafficking, and financial extortion. A Legitimate Interests Assessment (LIA) supports this minimal processing because:
  - Only public commercial claims are analyzed.
  - Recruiter personal data is limited to corporate email domains and professional names appearing on public recruitment adverts.
  - Processing is non-intrusive and produces no legal sanctions (verification results are informational guidance for the candidate).

### 2.2 Special Category & Biometric Data (Article 9)
- **Rule D Architecture:** LifeLens Ω **DOES NOT** collect, process, or store biometric data for the purpose of uniquely identifying a natural person (GDPR Article 9(1) / Article 4(14)).
- **Technical Artifacts vs. Biometrics:** The Meeting Shield analyzes communication channel characteristics:
  - Audio spectral power distribution (vocoder diffusion noise).
  - Packet jitter and timestamp delta (audio-video desynchronization).
  - High-frequency edge gradient anomalies in webcam rendering.
  These measurements quantify signal transmission fidelity rather than biological characteristics of an individual.

---

## 3. India Digital Personal Data Protection Act (DPDP Act 2023)

### 3.1 Notice and Consent (§5 & §6)
- The user is presented with a clear, standalone consent notice before starting verification or activating Meeting Shield.
- Processing is strictly limited to the specified purpose of recruitment fraud prevention.
- Users can withdraw consent at any time via the UI toggle ("Guard is off"), immediately halting stream processing.

### 3.2 Data Fiduciary Obligations (§8) & Erasure (§12)
- **Purpose Limitation:** Contact details extracted from job postings are never aggregated into marketing profiles, sold, or shared with third parties.
- **Data Minimization:** No raw audio or video chunks are persisted to disk or external databases. Processing is ephemeral and in-memory.
- **Erasure:** Upon conclusion of a verification session, in-memory buffers are flushed immediately.

---

## 4. Biometric Law Flags (Illinois BIPA, Texas CUBI, Washington)

| Jurisdiction & Law | Statutory Requirement | LifeLens Ω Engineering Compliance Status |
| :--- | :--- | :--- |
| **Illinois BIPA (740 ILCS 14/)** | Requires written release and prohibited storage of "biometric identifier" (retina scan, fingerprint, voiceprint, face geometry). | **COMPLIANT BY DESIGN:** LifeLens Ω does NOT capture face geometry templates or voiceprints. Neural face-swap boundary detectors inspect pixel gradient noise, not facial landmarks for identification. |
| **Texas CUBI (§ 503.001)** | Prohibits capturing biometric identifiers for commercial purposes without informed consent. | **COMPLIANT BY DESIGN:** Zero biometric identifiers captured. User gives explicit consent prior to real-time meeting stream inspection. |
| **California CCPA / CPRA** | Right to know, delete, and opt-out of sale of personal information. | **COMPLIANT:** No personal information is sold or shared with data brokers. Zero tracking cookies across web and extension surfaces. |

---

## 5. Outstanding Open Questions Requiring Legal Counsel

1. **Third-Party Participant Notice:** When a candidate activates Meeting Shield during a video call involving external recruiters, does local law in two-party consent states (e.g., California, Germany) require notifying all call participants that a client-side synthetic anomaly filter is running?
2. **Defamation & Trade Libel Defense (P1 Alignment):** By strictly adhering to Principle P1 ("Verification over Accusation") and Rule A (never labeling a person "scammer" or "fake", only reporting "Needs Verification" or "Company not found in registry"), does the system retain safe harbor against commercial defamation claims?
3. **Cross-Border Corridor Reporting:** When post-incident recovery packets are prepared for law enforcement (IC3, NCRP, Action Fraud), do cross-border data transfer restrictions apply to the victim's voluntary local report generation?
