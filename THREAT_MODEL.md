# LifeLens Ω — Threat Model & Security Baseline

**Document Version:** 2.0  
**Implements:** Implementation Plan §70, §71, §72, §73, §74, §75, §76, §92  

---

## 1. System Threat Landscape

LifeLens Ω is designed under adversarial assumptions. Adversaries seeking to evade detection or exploit the verification service fall into three classes:

1. **Deceptive Employers & Scammers:** Attempt to generate believable corporate personas, clone authentic domains (lookalike typosquatting), and leverage synthetic voice/video during remote interviews.
2. **Adversarial Evaders:** Intentionally craft postings that avoid explicit trigger keywords ("fee", "deposit") while introducing indirect pressure or obfuscated off-platform links.
3. **Malicious Network Actors:** Attempt Server-Side Request Forgery (SSRF) via malicious verification URLs, API denial-of-service, or poisoned community reports.

---

## 2. Threat Mitigations & Controls

### 2.1 SSRF Defense (§72)
- **Domain & IP Sanitizer:** All outgoing HTTP requests initiated by verification adapters must pass strict SSRF filters.
- **Private IP Rejection:** Blocks `127.0.0.1`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.169.254` (cloud metadata), and `localhost`.
- **Protocol Enforcement:** Only `https://` and approved `http://` protocols allowed; internal protocols (`file://`, `gopher://`) strictly rejected.

### 2.2 Extension Permission Security (§73)
- **Minimal Manifest Permissions:** LifeLens extension requests only `activeTab` and specific host permissions for supported job portals.
- **No Background Keylogging:** Extension content script runs only upon explicit user invocation ("Verify with LifeLens") or passive supported-page detection.

### 2.3 Secret Management (§74)
- Zero hardcoded credentials in codebase.
- Fallback mock adapters activate gracefully if environment API keys (`COMPANIES_HOUSE_API_KEY`, etc.) are absent.

### 2.4 Data Poisoning & Evasion Defense (§76, §97, §98)
- **Community Intel Salted HMAC:** Community threat patterns store domain hashes using keyed HMAC salts, preventing dictionary attacks.
- **Gradient Clipping & Outlier Rejection:** The Federated Privacy Sandbox clamps all parameter updates to a maximum gradient norm ($L_2 \le 1.5$) to prevent poisoning of baseline scoring metrics.

---

## 3. Red-Team Verification Matrix (§68)

| Threat Scenario | Attack Vector | LifeLens Ω Defense | Tested Status |
|-----------------|---------------|-------------------|---------------|
| **Typosquatting** | Lookalike domain (`acme-careers-hr.com`) | Domain comparison detects mismatch with registry official domain | ✅ PASS |
| **Fake Registry Claim** | Dissolved/Inactive company entity | Companies House adapter flags `CONTRADICTED` | ✅ PASS |
| **Urgent Visa Scam** | Upfront relocation visa payment request | Critical payment claim signal + trajectory escalation alert | ✅ PASS |
| **Off-Platform Shift** | Move LinkedIn chat to Telegram immediately | Contact claim detector flags off-platform transition | ✅ PASS |
| **Deepfake Interview** | Synthesized AI voice / face-swap | Meeting Shield detects spectral flatness & facial boundary distortion | ✅ PASS |

---

## 4. Internal Threat Modeling for LifeLens Systems (§Item 7)

This section models threats arising from the misuse or compromise of LifeLens Ω's own mechanisms and internal tools.

### 4.1 Abuse of the Trusted-Contact Broadcaster
* **Threat:** A malicious actor or compromised user account triggers repetitive emergency incident broadcasts or spoofed scam alerts to victim contacts, causing harassment, emotional distress, or alarm fatigue.
* **Mitigations:**
  - **Cryptographic Confirmation Gate:** Broadcasts require explicit, multi-step user confirmation with a cooldown delay before outbound delivery.
  - **Rate Limiting:** Maximum 3 contact notifications per 24-hour window per verified identity.
  - **No Automated Accusations (Rule A & P1):** Outbound messages contain neutral, standardized verification notices ("Verification step completed" or "Request looks high-risk"), never accusing individuals or transmitting raw transcripts.
  - **Recipient Opt-Out:** Every notification includes a cryptographic one-click unsubscribe mechanism that permanently blacklists the contact identifier from automated broadcasts.

### 4.2 Feedback Poisoning & Metric Manipulation
* **Threat:** Threat actors or fraudulent recruitment syndicates submit mass fabricated feedback (marking malicious offers as "legitimate" or authentic job offers as "scams") to degrade ML model calibration or clear entity warning flags.
* **Mitigations:**
  - **Proof-of-Work & Captcha Gating:** Feedback submissions require rate-limiting per IP/subnet and session verification.
  - **Independent Control Verification:** A scammer cannot clear a flagged entity simply by submitting a dispute or positive feedback; altering an entity's verified trust state requires independent proof of corporate control (e.g. DNS TXT record or verified email from the official domain registered in government databases).
  - **Federated Anomaly & Outlier Clamping:** Differential privacy noise ($\epsilon = 1.0$) and gradient norm clipping ($L_2 \le 1.5$) prevent clustered poisoned submissions from skewing global scoring baselines.

### 4.3 Stalking & Unmasking Misuse
* **Threat:** Stalkers, private investigators, or hostile parties use the verification engine, domain lookups, or community trust graph to de-anonymize victims, trace recruiter personal numbers, or link pseudonymous identities across platforms.
* **Mitigations:**
  - **Privacy by Default (P5):** Victim identifiers, personal candidate resumes, and contact lists are never stored in the trust graph.
  - **Salted One-Way Hashes:** Entity graph edges link public infrastructure identifiers (registrant ASNs, TLS certificates, corporate registration numbers), never private personal data.
  - **Query Sanitization:** Phone numbers and email usernames are normalized and hashed; personal phone numbers are never returned in public lookup APIs.

### 4.4 Ledger Tampering & History Rewriting
* **Threat:** A compromised administrator or adversary attempts to rewrite historical verification entries, erase proof of a fraudulent entity, or fabricate false verification receipts.
* **Mitigations:**
  - **Cryptographic Hash Chaining:** Every block in the `TrustIntegrityLedger` anchors the SHA-256 hash of the preceding block (`previous_hash`).
  - **Immutability Invariant:** Any mutation of past events invalidates the entire block chain verification test (`ledger.verify_chain_integrity() == False`).
  - **Public Verification Fingerprints:** High-risk incident reports and complaint packets include deterministic SHA-256 state fingerprints that can be independently recomputed from the evidence payload.
