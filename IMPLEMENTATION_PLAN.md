# LifeLens Ω — IMPLEMENTATION PLAN
## Team-Ready Product, Architecture & Engineering Roadmap

**Document Type:** Master Implementation Plan  
**Version:** 2.0  
**Status:** Implementation-ready / scope-controlled  
**Primary MVP:** Explainable Job & Foreign-Offer Verification  
**Long-Term Vision:** Privacy-aware, cross-platform trust verification  
**Audience:** Product, frontend, backend, data/ML, security, QA, research

---

# 0. Executive Direction

## Why This Revision Exists

The original LifeLens Ω implementation guide contains strong ideas:

- Entity → Claim → Evidence modelling
- CECT reasoning
- Evidence independence
- Behavioral consistency
- Trust trajectory
- Privacy controls
- Red-team testing
- Human-in-the-loop decisions

However, the original scope attempts to cover too many problems simultaneously:

```text
Scam Detection
+
Romance Scam Detection
+
Business Email Compromise
+
Payment Protection
+
Behavioral Baselines
+
Federated Learning
+
Deepfake Detection
+
Cross-Platform Analysis
+
Threat Intelligence
```

That is too broad for a first implementation.

The revised plan converts LifeLens Ω into a **focused product that can actually be built, tested, demonstrated, and extended**.

---

# 1. Product Strategy

## 1.1 Phase-1 Product

> **LifeLens Ω verifies whether a job posting or recruiter/foreign employment offer is supported by independent evidence and explains the reasons for its risk level.**

The first release is **not** a universal scam detector.

It is a:

```text
JOB + RECRUITER
        ↓
IDENTITY VERIFICATION
        ↓
CLAIM EXTRACTION
        ↓
INDEPENDENT EVIDENCE CHECK
        ↓
CECT ANALYSIS
        ↓
RISK + CONFIDENCE
        ↓
EXPLANATION
        ↓
USER DECISION
```

---

# 2. Core Differentiator

## Do Not Build

```text
Message
   ↓
AI
   ↓
SCAM / SAFE
```

## Build

```text
Job / Recruiter Interaction
          ↓
        Claims
          ↓
       Evidence
          ↓
 Independent Sources
          ↓
   CECT Analysis
          ↓
 Risk + Confidence
          ↓
 "Why?"
          ↓
 Safe Verification Path
```

The product value is therefore:

> **Detect → Verify → Explain → Empower**

The user remains the final decision-maker.

---

# 3. Product Principles

All implementation decisions must follow these principles.

## P1 — Verification over accusation

The product must prefer:

- `Needs Verification`
- `High Risk`
- `Evidence Missing`
- `Identity Mismatch`
- `Suspicious Pattern`

over absolute statements such as:

```text
"THIS PERSON IS A SCAMMER"
```

unless independently established by authoritative evidence.

---

## P2 — Signal ≠ Proof

A signal increases risk.

A signal does not automatically prove fraud.

Example:

```text
Recruiter uses Gmail
```

should become:

```text
Signal:
Recruiter email domain does not match the organization's official domain.

Interpretation:
Additional verification is recommended.

NOT:
The recruiter is fraudulent.
```

---

## P3 — Evidence must show provenance

Every important finding must answer:

```text
What was checked?
Where was it checked?
When was it checked?
What did the source say?
How reliable is the source?
Can the user independently verify it?
```

---

## P4 — No fake metrics

All project metrics must be classified as one of:

- `TARGET`
- `BENCHMARK`
- `MEASURED`
- `ILLUSTRATIVE`

Never present prototype targets as production achievements.

---

## P5 — Privacy by default

Do not collect a user's entire digital life just because the system could.

Phase 1 should only process data required for:

```text
job verification
recruiter verification
company verification
evidence verification
risk explanation
```

---

## P6 — Human-in-the-loop

LifeLens Ω provides evidence and reasoning.

The user decides whether to:

- Continue
- Verify
- Ask questions
- Report
- Ignore
- Apply
- Stop communication

---

# 4. Scope Control

## 4.1 Build Now — Phase 1

### Mandatory

- Chrome/Chromium browser extension
- Job-posting extraction
- Recruiter information extraction
- Company identity normalization
- Website/domain comparison
- Authoritative company-registry adapter
- Recruiter/agency verification where authoritative data is available
- Claim extraction
- Evidence ledger
- CECT scoring
- Transparent risk scoring
- Confidence scoring
- Explanation generation
- Verification checklist
- User feedback
- Audit logging
- Test dataset
- Red-team tests
- Privacy controls

---

## 4.2 Build Later — Phase 2

- Cross-platform identity graph
- Trust Graph
- Recruiter identity linkage
- Historical interaction analysis
- Trust trajectory analysis
- Community threat intelligence
- More country adapters
- More job boards
- Local device-side models

---

## 4.3 Build Later — Phase 3

- Voice/call analysis
- Desktop monitoring
- Audio/video authenticity analysis
- Third-party deepfake detection APIs
- Real-time meeting alerts

---

## 4.4 Do NOT Build in MVP

The following must not block Phase 1:

- WhatsApp video-call interception
- Universal social-media monitoring
- Full federated learning
- Training a large foundation model from scratch
- Full autonomous payment blocking
- Continuous monitoring of all private communications
- Global multi-country coverage from day one
- Fully autonomous fraud declarations
- Production-scale millions-of-users infrastructure

---

# 5. MVP User Journey

```text
1. User opens a job posting
              ↓
2. LifeLens extension detects supported page
              ↓
3. User clicks "Verify with LifeLens"
              ↓
4. Extension extracts job + recruiter + company data
              ↓
5. Backend normalizes entities and claims
              ↓
6. Verification adapters query authoritative sources
              ↓
7. Domain + identity + claim checks execute
              ↓
8. CECT engine evaluates:
       - Coherence
       - Evidence Independence
       - Consistency
       - Trajectory
              ↓
9. Risk engine produces:
       - Risk level
       - Confidence
       - Primary concerns
       - Evidence
              ↓
10. Extension displays explanation
              ↓
11. User chooses:
       - Verify more
       - Continue cautiously
       - Report
       - Ignore
              ↓
12. Feedback is stored for evaluation
```

---

# 6. High-Level Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                 BROWSER EXTENSION                       │
│                                                         │
│  Content Script                                         │
│  ├─ Detect supported job page                           │
│  ├─ Extract DOM content                                 │
│  ├─ Extract recruiter/company/job fields               │
│  └─ Send minimal required payload                       │
│                                                         │
│  Extension UI                                            │
│  ├─ Verify button                                       │
│  ├─ Risk summary                                        │
│  ├─ Evidence cards                                      │
│  └─ Explanation / safe verification actions            │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTPS
                        ▼
┌─────────────────────────────────────────────────────────┐
│                    API GATEWAY                           │
│                                                         │
│  Authentication / rate limiting / request validation   │
└───────────────────────┬─────────────────────────────────┘
                        │
            ┌───────────┼────────────────┐
            ▼           ▼                ▼
┌────────────────┐ ┌──────────────┐ ┌───────────────────┐
│ Extraction &   │ │ Verification │ │ Evidence Service  │
│ Normalization  │ │ Orchestrator │ │                   │
│                │ │              │ │ provenance        │
│ entities       │ │ company DB   │ │ source snapshots  │
│ claims         │ │ domains      │ │ timestamps        │
│ contacts       │ │ agencies     │ │ verification path │
└───────┬────────┘ └──────┬───────┘ └─────────┬─────────┘
        │                 │                    │
        └─────────────────┼────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  CECT REASONING ENGINE                  │
│                                                         │
│  Coherence          → claims fit together               │
│  Evidence Indep.    → evidence is independent           │
│  Consistency        → identity/domain/data align        │
│  Trajectory         → interaction is escalating risk    │
└───────────────────────┬─────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│                RISK + CONFIDENCE ENGINE                 │
│                                                         │
│  Risk signals                                           │
│  Signal reliability                                     │
│  Evidence strength                                      │
│  Data completeness                                      │
│  Confidence                                             │
│  Decision policy                                        │
└───────────────────────┬─────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│                 EXPLANATION SERVICE                     │
│                                                         │
│  What was checked?                                      │
│  What matched?                                          │
│  What could not be verified?                            │
│  Why does this increase risk?                           │
│  What should the user verify next?                      │
└───────────────────────┬─────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│                 USER DECISION LAYER                     │
│                                                         │
│  VERIFY | CONTINUE CAUTIOUSLY | REPORT | IGNORE        │
└─────────────────────────────────────────────────────────┘
```

---

# 7. Recommended Technical Stack

The team may replace individual technologies later, but the architecture must preserve the module boundaries.

## Frontend / Extension

```text
TypeScript
React
Manifest V3
Vite
```

Responsibilities:

- DOM extraction
- Supported-site detection
- UI
- API communication
- Local caching of non-sensitive state
- User controls

---

## Backend

```text
Python
FastAPI
Pydantic
SQLAlchemy
PostgreSQL
Redis
```

Responsibilities:

- API
- verification orchestration
- data normalization
- CECT
- risk engine
- evidence management
- feedback
- audit logging

---

## AI / NLP

Start with deterministic + small-model components.

```text
Phase 1:
Rules + structured extraction + embeddings / lightweight NLP

Phase 2:
Domain-specific classifiers

Phase 3:
More advanced local / hosted language models where justified
```

Do not start by training a large custom model.

---

## Infrastructure

Development:

```text
Docker Compose
```

Production-ready direction:

```text
Containerized services
Managed PostgreSQL
Managed Redis
Object storage for approved evidence artifacts
HTTPS
Centralized logging
Metrics / tracing
```

---

# 8. Repository Structure

```text
lifelens/
│
├── apps/
│   ├── extension/
│   │   ├── src/
│   │   │   ├── content/
│   │   │   ├── background/
│   │   │   ├── popup/
│   │   │   ├── components/
│   │   │   ├── services/
│   │   │   └── types/
│   │   └── manifest.json
│   │
│   └── api/
│       ├── app/
│       │   ├── api/
│       │   ├── models/
│       │   ├── schemas/
│       │   ├── services/
│       │   ├── repositories/
│       │   ├── verification/
│       │   ├── cect/
│       │   ├── risk/
│       │   ├── explanations/
│       │   └── security/
│       └── tests/
│
├── packages/
│   ├── schemas/
│   ├── scoring/
│   ├── source-adapters/
│   └── shared-types/
│
├── datasets/
│   ├── synthetic/
│   ├── legitimate/
│   ├── scam/
│   └── evaluation/
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── privacy/
│   ├── threat-model/
│   └── research/
│
├── infra/
│   ├── docker/
│   ├── migrations/
│   └── deployment/
│
├── scripts/
│
├── .env.example
├── docker-compose.yml
├── README.md
└── IMPLEMENTATION_PLAN.md
```

---

# 9. Canonical Data Model

The original Entity → Claim → Evidence abstraction is retained, but the data model is reduced to what the MVP actually needs.

## 9.1 VerificationRequest

```python
@dataclass
class VerificationRequest:
    request_id: str
    created_at: datetime

    source_platform: str

    job_title: Optional[str]
    job_description: Optional[str]

    company_name: Optional[str]
    company_website: Optional[str]

    recruiter_name: Optional[str]
    recruiter_email: Optional[str]
    recruiter_phone: Optional[str]

    claimed_country: Optional[str]
    claimed_location: Optional[str]

    consent_for_analysis: bool
```

---

# 10. Entity Model

```python
@dataclass
class Entity:
    entity_id: str
    entity_type: str

    claimed_name: Optional[str]
    claimed_role: Optional[str]

    email: Optional[str]
    phone: Optional[str]
    website: Optional[str]

    normalized_name: Optional[str]

    verification_status: str
    verification_confidence: float

    source_references: List[str]
```

Allowed verification states:

```text
UNKNOWN
PARTIALLY_VERIFIED
VERIFIED
CONTRADICTED
UNAVAILABLE
```

Do not map `UNAVAILABLE` directly to `FRAUD`.

---

# 11. Claim Model

```python
@dataclass
class Claim:
    claim_id: str

    entity_id: str

    claim_text: str
    claim_type: str

    source: str

    supporting_evidence_ids: List[str]
    contradicting_evidence_ids: List[str]

    verification_status: str

    confidence: float

    first_observed_at: datetime
    last_observed_at: datetime
```

Suggested claim types:

```text
IDENTITY
EMPLOYMENT
AUTHORITY
LOCATION
SALARY
VISA
RECRUITMENT
PAYMENT
DOCUMENT
URGENCY
CONTACT
WEBSITE
```

---

# 12. Evidence Model

```python
@dataclass
class Evidence:
    evidence_id: str

    source_type: str
    source_name: str
    source_url: Optional[str]

    observed_value: str

    captured_at: datetime

    source_authority: float
    source_independence: float

    user_verifiable: bool
    verification_path: Optional[str]

    evidence_strength: float

    source_status: str
```

`source_status`:

```text
AVAILABLE
UNAVAILABLE
STALE
CONFLICTING
NOT_APPLICABLE
```

---

# 13. Important Change: Evidence Ledger

The evidence ledger is a first-class object.

Every major risk statement should be traceable to evidence.

Example:

```text
Finding:
Recruiter identity is not independently verified.

Evidence:
- Recruiter claims to work for Company X.
- Company X official domain does not list the recruiter.
- Recruiter email uses a different domain.
- Registry confirms Company X exists.
```

This makes explanations auditable.

---

# 14. CECT Framework — MVP Definition

The CECT framework remains the core LifeLens Ω reasoning model.

## C — Coherence

Question:

> Do the claims logically fit together?

Examples:

```text
Claim:
"Company is based in Country A"

Job:
"Permanent office in Country B"

Website:
"Only Country C listed"
```

Potential coherence issue:

```text
Claim conflict detected
```

---

## E — Evidence Independence

Question:

> Is the evidence independent of the person making the claim?

Evidence priority:

```text
Authoritative public source
        ↓
Official company source
        ↓
Verified third-party source
        ↓
Independent public source
        ↓
Recruiter-provided evidence
        ↓
Unverified screenshot / forwarded document
```

This ordering is a design principle, not a universal truth ranking for every source.

---

## C — Consistency

Question:

> Do the identity, company, domain, location, role and contact details agree?

Example:

```text
Company:
Acme Technologies

Official domain:
acme.com

Recruiter email:
hr@acme.com

Job posting:
Acme Technologies

Result:
Consistent
```

Potential mismatch:

```text
Recruiter:
hr-acme-careers@gmail.com

Official site:
acme.com
```

Result:

```text
Needs additional verification
```

---

## T — Trajectory

Phase 1 uses trajectory only for the **job/recruiter journey**.

Example:

```text
Job discovered
      ↓
Recruiter contact
      ↓
Move off platform
      ↓
Request personal documents
      ↓
Request payment
      ↓
Create urgency
```

This does not prove fraud.

It indicates that the interaction has moved toward higher-risk actions.

---

# 15. CECT Output

```python
@dataclass
class CECTAssessment:
    coherence_score: float
    evidence_independence_score: float
    consistency_score: float
    trajectory_score: float

    confidence: float

    findings: List[str]

    supporting_evidence_ids: List[str]
    contradicting_evidence_ids: List[str]
```

---

# 16. Risk Engine

## 16.1 Replace Hardcoded Scoring With Configurable Signals

The original guide contains fixed weights embedded directly in code.

That should be replaced by configuration.

Example:

```yaml
signals:

  company_not_found:
    severity: high
    default_weight: 0.25

  official_domain_mismatch:
    severity: medium
    default_weight: 0.15

  recruiter_unverified:
    severity: medium
    default_weight: 0.15

  upfront_payment_request:
    severity: critical
    default_weight: 0.30

  visa_claim_unverified:
    severity: medium
    default_weight: 0.10

  urgency_pressure:
    severity: medium
    default_weight: 0.05
```

These values are **initial prototype configuration**, not validated statistical probabilities.

They must be evaluated and recalibrated using test data.

---

# 17. Signal Object

```python
@dataclass
class RiskSignal:
    signal_id: str

    category: str

    description: str

    severity: str

    reliability: float

    evidence_ids: List[str]

    detected_by: str
```

---

# 18. Risk Calculation

Use the following conceptual model:

```text
Risk
=
Signal Severity
×
Signal Reliability
×
Evidence Strength
×
Context Adjustment
```

Then apply calibrated aggregation.

Do not interpret the final number as:

```text
"Probability that this is definitely a scam"
```

unless statistical calibration establishes that interpretation.

---

# 19. Risk Levels

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Suggested product behavior:

| Risk | UI | User Action |
|---|---|---|
| LOW | No interruption / small indicator | Normal review |
| MEDIUM | Caution notice | Verify key claims |
| HIGH | Strong warning | Verify independently before proceeding |
| CRITICAL | Friction + prominent warning | Stop and verify before payment/documents |

---

# 20. Confidence Is Separate From Risk

This is an important architectural change.

A result can be:

```text
Risk = HIGH
Confidence = LOW
```

meaning:

> There are several concerning signals, but the evidence is incomplete.

Or:

```text
Risk = MEDIUM
Confidence = HIGH
```

meaning:

> The system has high confidence in the observed evidence, but the evidence does not indicate severe risk.

Never collapse these two concepts into one number.

---

# 21. Explanation Engine

Every result must contain:

## What We Checked

```text
Company identity
Recruiter identity
Website domain
Job location
Claims
Independent evidence
```

## What We Found

```text
Company was found in the selected registry.
Recruiter identity could not be independently verified.
Recruiter email domain differs from official company domain.
```

## Why It Matters

```text
The mismatch makes the recruiter identity harder to verify.
This is a risk signal, not proof of fraud.
```

## What To Do Next

```text
Contact the company using contact information
from its official website rather than using the recruiter-provided link.
```

---

# 22. Explanation Template

```text
Risk Level: HIGH
Confidence: MEDIUM

Why this result?

1. [Finding]
   Evidence: [source]

2. [Finding]
   Evidence: [source]

3. [Finding]
   Evidence: [source]

What could not be verified?

- [Missing information]

Recommended next step:

- [Independent verification action]

Important:

A risk signal is not proof of fraud.
Verify independently before sending money or sensitive documents.
```

---

# 23. Verification Adapter Architecture

Do not hard-code every country's logic into the main verification engine.

Use adapters.

```python
class VerificationAdapter(Protocol):

    def supports(self, country: str) -> bool:
        ...

    def verify_company(self, name: str, **kwargs) -> VerificationResult:
        ...

    def verify_recruiter(self, **kwargs) -> VerificationResult:
        ...

    def build_verification_path(self, result) -> str:
        ...
```

---

# 24. Adapter Types

```text
BusinessRegistryAdapter
GovernmentGuidanceAdapter
RecruitmentLicenseAdapter
OfficialCompanyWebsiteAdapter
DomainAdapter
JobBoardAdapter
Embassy / Labor Information Adapter
```

Each adapter must report:

```text
source
timestamp
status
result
confidence
verification URL/path
error
```

---

# 25. Failure Handling

External sources will fail.

Possible states:

```text
TIMEOUT
RATE_LIMITED
NOT_FOUND
ACCESS_DENIED
TEMPORARY_ERROR
SOURCE_UNAVAILABLE
PARSER_ERROR
CONFLICTING_RESULT
```

Do not convert technical failure into a risk accusation.

Example:

```text
Bad:
"Company is fraudulent because registry API failed."

Correct:
"Company could not be verified because the registry source
was temporarily unavailable."
```

---

# 26. Domain Verification

The MVP should compare:

```text
Official Company Domain
        vs
Recruiter Email Domain
        vs
Job Posting Website
        vs
Links in Recruiter Message
```

Example:

```text
Official:
company.com

Recruiter:
careers@company.com

Result:
Consistent
```

Potential warning:

```text
Official:
company.com

Recruiter:
company-careers.example

Result:
Domain mismatch
```

A mismatch is a verification signal, not automatic proof of fraud.

---

# 27. URL Safety Layer

Every external link should be normalized.

Store:

```text
original_url
normalized_domain
final_domain
redirect_chain
https_status
domain_match_status
```

Never silently follow potentially dangerous content without sandboxing or safe request controls on the server.

---

# 28. Job Claim Extraction

Extract structured claims from job descriptions.

Example:

```text
Input:
"Work in Country X.
Visa sponsored.
Salary ₹2,00,000/month.
No experience required.
Join within 3 days.
Send passport copy to recruiter."
```

Extract:

```json
{
  "location_claim": "Country X",
  "visa_claim": true,
  "salary_claim": "₹2,00,000/month",
  "experience_claim": "No experience required",
  "urgency_claim": "Join within 3 days",
  "document_request": "passport copy"
}
```

---

# 29. Claim Normalization

Normalize:

- Currency
- Country
- Organization names
- URLs
- Email domains
- Phone numbers
- Dates
- Job titles
- Recruiter roles

The normalized representation becomes the input to verification.

---

# 30. No "Intent Detection" in MVP

The original guide contains a component called:

```text
Game-Theoretic Intent Scoring
```

This should not be a core MVP module.

Reason:

```text
Observed behavior
≠
Certain knowledge of someone's private intent
```

Replace it with:

```text
Risk Signal Extraction
```

The system should describe observable behavior:

```text
"Requests upfront payment."
"Discourages independent verification."
"Identity is not independently verified."
```

instead of:

```text
"Person is manipulative."
```

---

# 31. Behavioral Baselines — Deferred

The original guide includes detailed behavioral baselines.

These are conceptually valuable but should move to Phase 2.

## Why

They create:

- Privacy complexity
- Cold-start problems
- Consent complexity
- Baseline poisoning risk
- Larger data requirements
- Greater false-positive risk
- More compute

---

# 32. Phase-2 Behavioral Baseline

When introduced, it must be:

```text
Optional
Local-first
User-controlled
Minimum-data
Confidence-aware
Resettable
Explainable
```

Never use a weak baseline as strong evidence.

Example:

```text
Baseline confidence:
LOW

Result:
Behavioral signal disabled.
```

---

# 33. MVP Privacy Architecture

## Data Minimization

Send only:

```text
Job data required for verification
Recruiter data required for verification
Claim text required for analysis
```

Do not send:

```text
entire browser history
all messages
all contacts
background screenshots
unrelated browsing information
```

---

# 34. Privacy Data Classes

## Tier 1 — Request Data

Short-lived.

Examples:

- Job description
- Recruiter name
- Company name
- URLs

Retention:

```text
Short-lived / configurable
```

---

## Tier 2 — Verification Metadata

Examples:

- Verification results
- Evidence references
- Risk signals
- User feedback

Retention:

```text
User-controlled / defined product policy
```

---

## Tier 3 — Aggregate Intelligence

Examples:

- Anonymous scam pattern counts
- Domain patterns
- Aggregate false-positive statistics

Must not contain:

- User identity
- Raw private conversations
- Unnecessary personal data

---

# 35. Consent Model

Before analysis:

```text
[ ] I allow LifeLens to analyze this job/recruiter information.
```

For optional learning:

```text
[ ] I allow anonymous feedback to improve detection.
```

These must be separate choices.

Do not bundle all processing into one consent.

---

# 36. Security Requirements

## Mandatory MVP

- HTTPS
- Strict CORS
- Input validation
- Authentication where required
- API rate limits
- Secret management
- SQL injection protection
- Output encoding
- SSRF protection
- URL allow/deny controls
- Audit logging
- Dependency scanning
- Secure extension permissions

---

# 37. Extension Security

Request the minimum browser permissions required.

Avoid broad permissions such as:

```text
read all websites
```

unless absolutely necessary.

Preferred model:

```text
Supported job site
       ↓
User activates LifeLens
       ↓
Extract current page only
```

---

# 38. SSRF Protection

The backend may need to fetch websites.

This is a security-sensitive capability.

Implement:

```text
URL validation
+
DNS resolution controls
+
Private IP blocking
+
Redirect validation
+
Protocol restrictions
+
Timeouts
+
Response-size limits
+
Content-type validation
```

---

# 39. Database Schema

Recommended initial tables:

```text
users
verification_requests
entities
claims
evidence
risk_signals
cect_assessments
verification_sources
user_feedback
audit_events
adapter_runs
```

---

# 40. Core Relationships

```text
verification_request
        │
        ├── entities
        │      │
        │      └── claims
        │              │
        │              └── evidence
        │
        ├── verification_sources
        │
        ├── cect_assessment
        │
        ├── risk_signals
        │
        └── user_feedback
```

---

# 41. API Specification

## POST `/api/v1/verifications`

Start a verification.

```json
{
  "source_platform": "supported_job_board",
  "job_title": "Software Engineer",
  "company_name": "Example Technologies",
  "company_website": "https://example.com",
  "recruiter_name": "Recruiter Name",
  "recruiter_email": "recruiter@example.com",
  "claimed_country": "Country",
  "job_description": "..."
}
```

Response:

```json
{
  "request_id": "uuid",
  "status": "PROCESSING"
}
```

---

## GET `/api/v1/verifications/{request_id}`

Response:

```json
{
  "request_id": "uuid",
  "status": "COMPLETE",
  "risk_level": "HIGH",
  "confidence": "MEDIUM",
  "cect": {
    "coherence": 0.62,
    "evidence_independence": 0.31,
    "consistency": 0.48,
    "trajectory": 0.40
  },
  "primary_concerns": [],
  "evidence": [],
  "recommended_actions": []
}
```

The numerical values above are **example response values only**.

---

## POST `/api/v1/feedback`

Collect user feedback.

```json
{
  "request_id": "uuid",
  "feedback_type": "false_positive",
  "comment": "The recruiter was legitimate.",
  "confirmed_outcome": "LEGITIMATE"
}
```

Do not automatically treat user feedback as ground truth.

---

# 42. CECT Pipeline

```text
Raw Job / Recruiter Data
          ↓
Normalization
          ↓
Claim Extraction
          ↓
Evidence Collection
          ↓
Evidence Source Classification
          ↓
Coherence Analysis
          ↓
Evidence Independence Analysis
          ↓
Identity / Domain Consistency Analysis
          ↓
Trajectory Analysis
          ↓
CECT Assessment
          ↓
Risk Engine
          ↓
Confidence Engine
          ↓
Explanation Engine
```

---

# 43. Coherence Engine

Start with:

```text
structured rules
+
entity matching
+
semantic similarity
+
explicit contradiction rules
```

Do not use simple keyword rules as the only reasoning mechanism.

---

# 44. Contradiction Detection

Examples:

```text
Company location:
London

Job description:
Permanent position in New York

Official company page:
Operations only in London

Potential contradiction:
YES
```

But the engine should distinguish:

```text
DIRECT CONTRADICTION
MISSING INFORMATION
POSSIBLE EXPLANATION
UNVERIFIED
```

This prevents over-accusation.

---

# 45. Evidence Independence Engine

Evidence receives dimensions:

```text
Source Independence
Source Authority
Verifiability
Freshness
Relevance
Consistency
```

Example:

```text
Recruiter screenshot:
independence = low

Official registry:
independence = high

Official company website:
independence = medium/high
```

The exact values should be configuration-driven and empirically evaluated.

---

# 46. Consistency Engine

Check relationships among:

```text
Company name
Official company name
Website
Recruiter email
Recruiter role
Job location
Job board
Contact details
Claimed visa information
Recruitment agency
```

Output:

```text
CONSISTENT
PARTIALLY_CONSISTENT
CONFLICTING
INSUFFICIENT_DATA
```

---

# 47. Trajectory Engine

Phase 1 tracks risk escalation when a user supplies recruiter interaction context.

Example:

```text
Stage 1 — Job posting
Stage 2 — Recruiter contact
Stage 3 — Off-platform move
Stage 4 — Sensitive document request
Stage 5 — Payment request
Stage 6 — Urgency / pressure
```

Trajectory output:

```text
STABLE
INCREASING
HIGH_RISK_ESCALATION
INSUFFICIENT_DATA
```

---

# 48. Recommended Actions

The action engine should never simply mirror risk.

Example:

```text
HIGH RISK
+
LOW CONFIDENCE
=
VERIFY MORE
```

Example:

```text
CRITICAL SIGNAL
+
HIGH EVIDENCE STRENGTH
=
STOP AND VERIFY BEFORE PROCEEDING
```

Actions:

```text
REVIEW
VERIFY
VERIFY_INDEPENDENTLY
DO_NOT_SEND_MONEY
DO_NOT_SEND_SENSITIVE_DOCUMENTS
REPORT
```

---

# 49. User Experience

## Browser Card

```text
┌───────────────────────────────────────┐
│          LIFE LENS Ω                  │
│       Job Verification               │
├───────────────────────────────────────┤
│ Risk: HIGH                            │
│ Confidence: MEDIUM                    │
│                                       │
│ ⚠ Recruiter identity not verified    │
│ ⚠ Email domain mismatch              │
│ ⚠ Visa claim not independently       │
│   verified                            │
│                                       │
│ ✓ Company exists in registry         │
│                                       │
│ [See Evidence] [Verify Safely]       │
└───────────────────────────────────────┘
```

---

# 50. Evidence View

```text
┌───────────────────────────────────────┐
│ WHY DID LIFE LENS FLAG THIS?          │
├───────────────────────────────────────┤
│                                       │
│ 1. Recruiter identity                 │
│    Status: Unverified                 │
│    Source checked: Official company   │
│    directory                          │
│                                       │
│ 2. Domain                             │
│    Recruiter: example-careers.com     │
│    Official: example.com              │
│    Result: Mismatch                   │
│                                       │
│ 3. Company                            │
│    Registry: Found                    │
│                                       │
│ [Open Verification Path]              │
└───────────────────────────────────────┘
```

---

# 51. Verification Path

The user should receive a concrete safe verification route.

Example:

```text
1. Open the organization's official website.
2. Navigate to the official careers/contact page.
3. Find the published contact details.
4. Contact the organization independently.
5. Ask whether the recruiter and job are genuine.
6. Continue only after the important claims are confirmed.
```

The system should prefer user-verifiable actions instead of asking the user to trust LifeLens blindly.

---

# 52. MVP Feature Priorities

| Feature | Priority | Phase |
|---|---|---|
| Browser extraction | P0 | 1 |
| Entity normalization | P0 | 1 |
| Company verification | P0 | 1 |
| Domain comparison | P0 | 1 |
| Claim extraction | P0 | 1 |
| Evidence ledger | P0 | 1 |
| CECT engine | P0 | 1 |
| Risk engine | P0 | 1 |
| Explainability | P0 | 1 |
| Privacy controls | P0 | 1 |
| User feedback | P1 | 1 |
| Multiple country adapters | P1 | 1/2 |
| Trust Graph | P1 | 2 |
| Behavioral baseline | P2 | 2 |
| Community intelligence | P2 | 2 |
| Video detection | P3 | 3 |
| Federated learning | P3 | 3 |

---

# 53. Team Responsibilities

## Product / Research Lead

Own:

- Problem definition
- Scope
- Evaluation criteria
- Research questions
- Country/source selection
- User interviews
- Product decisions

---

## Extension Developer

Own:

- Browser extension
- DOM extraction
- Supported-site adapters
- Popup/UI
- Content scripts
- Browser permission model
- Extension testing

---

## Backend Developer

Own:

- API
- Database
- verification orchestration
- source adapters
- caching
- authentication
- rate limiting
- audit logs

---

## AI / ML Engineer

Own:

- Claim extraction
- Semantic similarity
- CECT engines
- Risk signal extraction
- Confidence modelling
- Evaluation datasets
- Model evaluation

---

## Security Engineer

Own:

- Threat model
- SSRF protection
- Extension security
- API security
- dependency scanning
- privacy review
- red-team scenarios

---

## QA Engineer

Own:

- Functional testing
- Regression testing
- Browser compatibility
- Adversarial test suite
- False-positive evaluation
- Performance testing

---

# 54. If the Team Is Small

For a 3–4 person team:

```text
Person 1:
Frontend + Extension

Person 2:
Backend + Database + Integrations

Person 3:
AI/ML + CECT + Evaluation

Person 4:
Security + QA + DevOps + Product support
```

For a 2-person team:

```text
Person 1:
Extension + UI + product

Person 2:
Backend + CECT + AI + infrastructure
```

Security/QA becomes a shared responsibility.

---

# 55. Development Phases

## Phase 0 — Source & Feasibility Audit

Before coding deeply, create a source matrix.

```text
Country
   ↓
Official company registry
   ↓
Recruitment licensing source
   ↓
Labor / visa source
   ↓
Official government guidance
   ↓
API available?
   ↓
Terms allow automated access?
   ↓
Data freshness?
```

Deliverable:

```text
SOURCE_CATALOG.md
```

---

# 56. Phase 0 Acceptance Criteria

Do not begin large-scale implementation until:

- At least one authoritative company-verification source is identified.
- Access method is documented.
- Usage constraints are documented.
- Data fields are mapped.
- Failure conditions are understood.
- One pilot country/workflow is selected.
- At least three representative job-scam scenarios are defined.
- At least three legitimate job scenarios are defined.

---

# 57. Phase 1 — Foundation

Build:

```text
Repository
Database
API
Extension shell
Shared schemas
Logging
Basic authentication
Docker environment
```

Deliverables:

```text
/api/health
Extension loads
Database migrations work
CI pipeline works
Basic request flows end-to-end
```

---

# 58. Phase 2 — Extraction

Implement:

```text
Job title extraction
Company extraction
Recruiter extraction
Email extraction
Website extraction
Country/location extraction
Job description extraction
```

Create extraction confidence:

```text
HIGH
MEDIUM
LOW
```

Low-confidence extraction should be visible to the reasoning engine.

---

# 59. Phase 3 — Verification

Implement:

```text
Company lookup
Official website lookup
Domain comparison
Recruiter verification
Source provenance
Timestamping
Caching
Failure handling
```

Deliverable:

```text
VerificationResult
```

---

# 60. Phase 4 — CECT

Implement in order:

```text
1. Coherence
2. Evidence Independence
3. Consistency
4. Trajectory
```

Do not build an advanced ML model before the deterministic reasoning layer works.

Reason:

```text
Transparent baseline
        ↓
Evaluation data
        ↓
Measured weaknesses
        ↓
ML upgrade
```

---

# 61. Phase 5 — Risk + Explanation

Implement:

```text
Risk signals
Signal weighting
Confidence
Risk levels
Primary concerns
Evidence cards
Verification paths
User feedback
```

Output must always be explainable.

---

# 62. Phase 6 — Evaluation

Create a fixed evaluation dataset.

Suggested categories:

```text
Legitimate company
Legitimate recruiter
Third-party recruiter
New company with weak web presence
Fake company
Impersonated company
Domain mismatch
Fake visa promise
Upfront-fee request
Fake employment contract
Urgency pressure
Cross-border offer
```

---

# 63. Evaluation Metrics

The team must measure:

## Extraction

- Field accuracy
- Missing-field rate

## Verification

- Verification success rate
- Source failure rate
- Source freshness

## Risk

- Precision
- Recall
- F1
- False-positive rate
- False-negative rate

## User Experience

- Time to result
- Explanation comprehension
- Verification-path completion
- User override rate

## Performance

- p50 latency
- p95 latency
- p99 latency
- API error rate

Never report a single "accuracy" number without defining:

```text
dataset
class distribution
evaluation protocol
time period
```

---

# 64. Target Metrics — Not Achieved Metrics

Initial targets can be stored as:

```yaml
targets:
  p95_verification_latency_ms: 3000
  extraction_field_accuracy: 0.90
  false_positive_rate: "<=0.05"
  explanation_comprehension: ">=0.80"
```

These are **engineering targets only**.

They must not be presented as achieved performance until measured.

---

# 65. Base-Rate Evaluation

Do not create a dataset containing 50% scams and 50% legitimate jobs and claim that performance represents the real world.

Also evaluate realistic prevalence scenarios.

Example:

```text
Large legitimate-job pool
+
smaller scam pool
```

Track:

```text
precision
alert volume
false alerts per 1,000 verified jobs
```

This gives the team a better understanding of user impact.

---

# 66. Red-Team Framework

Create attacks that intentionally evade obvious rules.

## Test Categories

```text
A. Keyword substitution
B. Rephrased payment request
C. Fake official-looking evidence
D. Lookalike domain
E. Recruiter impersonation
F. Legitimate third-party recruiter
G. New legitimate company
H. Foreign-country source unavailable
I. Conflicting registry information
J. Multi-stage escalation
```

---

# 67. Adversarial Examples

Bad detector:

```text
"Send payment now"
```

Attacker changes to:

```text
"Complete the mandatory processing contribution
before the onboarding deadline."
```

The system should still detect the **underlying risk pattern** where evidence supports it.

Therefore the model must increasingly move from:

```text
keyword matching
```

toward:

```text
claim semantics
+
entity relationships
+
evidence
+
context
```

---

# 68. Red-Team Acceptance Criteria

For every adversarial scenario, store:

```text
scenario_id
input
expected_signals
expected_risk_range
actual_result
detection_stage
explanation_quality
failure_reason
```

A failed red-team test becomes an engineering ticket.

---

# 69. Regression Testing

Every bug that reaches production-like testing must become a permanent regression case.

Example:

```text
BUG-014:
Legitimate third-party recruiter incorrectly flagged
```

Add it to:

```text
datasets/evaluation/regression/
```

The system must pass old regression cases before new releases.

---

# 70. Observability

Minimum telemetry:

```text
request_count
verification_success_rate
adapter_error_rate
adapter_latency
p50/p95/p99 latency
risk_level_distribution
feedback_distribution
explanation_open_rate
verification_path_open_rate
```

Do not collect raw private content merely to improve dashboards.

---

# 71. Monitoring Alerts

Example:

```text
IF adapter_error_rate > threshold
    alert integration owner

IF p95_latency > threshold
    alert backend owner

IF false_positive_rate > threshold
    freeze risk-rule release

IF source data changes unexpectedly
    disable adapter

IF privacy event occurs
    trigger incident process
```

Thresholds must be configured per environment.

---

# 72. Audit Logging

Record:

```text
who
what
when
which source
which adapter
which version
which rule/model
which result
```

Do not log:

- passwords
- private authentication tokens
- unnecessary full message content
- sensitive user information without need

---

# 73. Model / Rule Versioning

Every assessment must know:

```text
cect_version
risk_config_version
extraction_version
adapter_version
source_version
```

Example:

```json
{
  "cect_version": "0.1.0",
  "risk_config_version": "0.3.2",
  "extractor_version": "0.2.1"
}
```

This allows reproducibility.

---

# 74. Release Strategy

## Development

```text
Feature branch
      ↓
Unit tests
      ↓
Integration tests
      ↓
Security checks
      ↓
Evaluation dataset
      ↓
Code review
```

## Release

```text
Canary
  ↓
Small internal group
  ↓
Measure
  ↓
Rollback if needed
  ↓
Wider rollout
```

---

# 75. Kill Switches

The system must support disabling:

```text
specific rule
specific model
specific source adapter
specific country adapter
specific feature
```

without taking the entire product offline.

---

# 76. Data Quality Gates

Before a verification source is used in production, validate:

```text
Coverage
Freshness
Consistency
Availability
Terms / access constraints
Error behavior
```

If a source is degraded:

```text
source status = DEGRADED
```

rather than silently producing false results.

---

# 77. Country Adapter Strategy

Do not promise "all countries" initially.

Implement:

```text
Country Adapter Interface
        ↓
Pilot Country Adapter
        ↓
Evaluation
        ↓
Second Country
        ↓
Reusable Adapter Pattern
```

Every adapter must have:

```text
SOURCE_CATALOG.md
API / access documentation
Field mapping
Known limitations
Test cases
Fallback behavior
```

---

# 78. Foreign Offer Verification Pipeline

```text
Claimed employer
       ↓
Company existence
       ↓
Company identity
       ↓
Official domain
       ↓
Recruiter / agency identity
       ↓
Employment claim
       ↓
Visa / work authorization claim
       ↓
Official government information
       ↓
Contract / fee / urgency signals
       ↓
CECT
       ↓
Risk + explanation
```

The system should not provide legal immigration advice.

It should point users toward authoritative sources.

---

# 79. Document Verification

Phase 1 may accept:

- Job letter
- Offer letter
- Recruiter email
- Screenshot
- PDF

But the first version should primarily verify **claims and provenance**, not promise perfect forgery detection.

Example:

```text
Document claims:
"Visa is guaranteed."

Verification:
Government source does not independently support the claim.

Result:
Claim not independently verified.
```

---

# 80. Deepfake / Video Feature — Future Architecture

Only after Phase 1 has traction.

```text
Desktop Agent
      ↓
Screen / Audio Capture
      ↓
Consent Gate
      ↓
Third-Party Detection API
      ↓
Authenticity Signals
      ↓
LifeLens Evidence Layer
      ↓
Risk + Explanation
      ↓
User Alert
```

Do not train a custom deepfake model in the MVP.

---

# 81. Cross-Platform Trust Graph — Phase 2

Long-term architecture:

```text
                 ┌──────────────┐
                 │    PERSON    │
                 └──────┬───────┘
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
    LinkedIn         Email             Phone
        │               │                │
        └───────────────┼────────────────┘
                        ▼
                 Identity Graph
                        │
       ┌────────────────┼─────────────────┐
       ▼                ▼                 ▼
   Company          Website          Recruiter
       │                │                 │
       └────────────────┼─────────────────┘
                        ▼
                  Trust Analysis
                        │
              Evidence + CECT
```

This is the longer-term originality layer.

---

# 82. Community Threat Intelligence — Phase 2

Create anonymized pattern intelligence.

Example:

```text
SCAM_PATTERN_001
Pattern:
Upfront visa-processing fee

Affected geography:
Country / region

Observed domains:
Hashed / privacy-safe representation

Confidence:
Medium

Reports:
N
```

Do not expose private user data.

---

# 83. Trust Trajectory — Phase 2

Instead of classifying one event:

```text
Safe / Scam
```

model change over time:

```text
Initial Contact
      ↓
Trust Building
      ↓
Off-Platform Move
      ↓
Sensitive Information
      ↓
Financial Request
      ↓
Pressure
```

Output:

```text
Trajectory:
STABLE
INCREASING RISK
HIGH-RISK ESCALATION
```

---

# 84. Original Research Opportunity

The strongest research direction is not "another scam classifier."

It is:

> **Evidence-grounded trust trajectory modelling.**

Research question:

```text
Can a system identify when an interaction becomes
progressively less independently verifiable before
the final harmful action occurs?
```

Possible contribution:

```text
Claim graph
+
Evidence graph
+
Identity consistency
+
Trajectory
=
Trust Integrity Model
```

---

# 85. Proposed LifeLens Ω Trust Integrity Model

```text
               CLAIMS
                  │
                  ▼
           ┌──────────────┐
           │ EVIDENCE     │
           │ GRAPH        │
           └──────┬───────┘
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
   Coherence   Evidence   Consistency
       │      Independence     │
       └──────────┬────────────┘
                  ▼
              Trajectory
                  │
                  ▼
          Trust Integrity
                  │
                  ▼
       Explainable User Decision
```

This can eventually become the central research identity of LifeLens Ω.

---

# 86. What the Team Should NOT Claim Yet

Until supported by real experiments, do not claim:

```text
"Industry-grade"
"Production proven"
"95% accurate"
"Detects all scams"
"Understands human intent"
"Knows whether someone is lying"
"Prevents all fraud"
"Works for millions of users"
"Works for every country"
```

Use:

```text
Prototype
Research implementation
Pilot
Target
Measured benchmark
```

where appropriate.

---

# 87. Demo Scenario

The team should create one polished end-to-end scenario.

## Scenario

A foreign job recruiter contacts a candidate.

```text
Job:
Software Engineer — Country X

Claim:
"Visa sponsorship included."

Recruiter:
"HR Manager"

Email:
hr-careers@example-careers.com

Official company:
example.com
```

LifeLens checks:

```text
Company exists → YES

Official website → YES

Recruiter identity → NOT VERIFIED

Domain match → NO

Visa claim → NOT INDEPENDENTLY VERIFIED

Urgency → YES

Payment request → YES
```

CECT:

```text
Coherence:
MEDIUM

Evidence Independence:
LOW

Consistency:
LOW

Trajectory:
HIGH RISK
```

Final UI:

```text
Risk: HIGH
Confidence: MEDIUM

Primary concerns:
1. Recruiter identity not independently verified.
2. Recruiter domain differs from official company domain.
3. Visa claim is not independently verified.
4. Interaction is moving toward a financial request.

Next step:
Contact the company through its official website.
Do not send money or sensitive documents until verified.
```

---

# 88. Team Definition of Done

A feature is complete only when:

```text
Code exists
+
Unit tests pass
+
Integration tests pass
+
Security reviewed
+
Failure states handled
+
Logs/metrics added
+
Documentation updated
+
Evaluation case added
+
User-facing explanation tested
```

---

# 89. MVP Definition of Done

LifeLens Ω Phase 1 is complete when a user can:

```text
Open supported job posting
        ↓
Run LifeLens verification
        ↓
Receive company/recruiter verification
        ↓
See evidence
        ↓
See CECT reasoning
        ↓
See risk + confidence
        ↓
Understand why
        ↓
Follow an independent verification path
        ↓
Submit feedback
```

---

# 90. Suggested 6-Week Team Sprint

## Week 1 — Foundation

```text
- Repo
- Architecture
- Database
- Extension shell
- API skeleton
- Source audit
- Threat model
```

Deliverable:

```text
End-to-end "Verify" button
```

---

## Week 2 — Extraction

```text
- Job extraction
- Company extraction
- Recruiter extraction
- URL/email normalization
- Extraction confidence
```

Deliverable:

```text
Structured VerificationRequest
```

---

## Week 3 — Verification

```text
- Company source adapter
- Official website lookup
- Domain comparison
- Evidence ledger
- Adapter failures
```

Deliverable:

```text
VerificationResult
```

---

## Week 4 — CECT + Risk

```text
- Coherence
- Evidence independence
- Consistency
- Trajectory
- Risk signals
- Confidence
```

Deliverable:

```text
CECTAssessment
```

---

## Week 5 — UX + Security

```text
- Risk card
- Evidence view
- Explanation
- Safe verification path
- Consent
- SSRF protection
- Permission review
- Audit logs
```

Deliverable:

```text
Polished end-to-end MVP
```

---

## Week 6 — Evaluation + Demo

```text
- Legitimate dataset
- Scam dataset
- Red-team tests
- Regression tests
- Performance measurements
- False-positive analysis
- Demo scenario
- Documentation
```

Deliverable:

```text
MVP v0.1
```

---

# 91. Engineering Tickets — P0

## Extension

```text
EXT-001 Create Manifest V3 app
EXT-002 Detect supported job pages
EXT-003 Extract company
EXT-004 Extract recruiter
EXT-005 Extract job description
EXT-006 Normalize URLs/emails
EXT-007 Add Verify UI
EXT-008 Render risk result
EXT-009 Render evidence cards
EXT-010 Render verification path
```

## Backend

```text
API-001 Create FastAPI project
API-002 Create PostgreSQL schema
API-003 Create verification endpoint
API-004 Create verification status endpoint
API-005 Create feedback endpoint
API-006 Add request validation
API-007 Add rate limiting
API-008 Add audit logging
```

## Verification

```text
VER-001 Define adapter interface
VER-002 Implement company registry adapter
VER-003 Implement official website adapter
VER-004 Implement domain comparison
VER-005 Implement source provenance
VER-006 Implement cache
VER-007 Implement adapter failure handling
```

## AI / Reasoning

```text
ML-001 Claim schema
ML-002 Claim extractor
ML-003 Coherence engine
ML-004 Evidence independence engine
ML-005 Consistency engine
ML-006 Trajectory engine
ML-007 Risk signal engine
ML-008 Confidence engine
ML-009 Explanation engine
ML-010 Evaluation harness
```

## Security / QA

```text
SEC-001 Threat model
SEC-002 SSRF protection
SEC-003 Extension permissions audit
SEC-004 Secret management
SEC-005 Dependency scan
QA-001 Unit tests
QA-002 Integration tests
QA-003 Browser tests
QA-004 Red-team tests
QA-005 Regression suite
QA-006 Performance tests
```

---

# 92. Documentation the Team Must Maintain

```text
README.md
IMPLEMENTATION_PLAN.md
ARCHITECTURE.md
API.md
DATA_MODEL.md
SOURCE_CATALOG.md
THREAT_MODEL.md
PRIVACY.md
EVALUATION.md
RED_TEAM.md
CHANGELOG.md
```

---

# 93. Decision Log

Every major architecture decision should be recorded.

Template:

```markdown
## ADR-001 — Why Job Verification Is Phase 1

### Decision
Build explainable job/recruiter verification before video-call detection.

### Reason
Smaller scope, easier integration, clearer user problem, stronger
cross-border verification differentiation.

### Alternatives Considered
- Universal scam detector
- Video deepfake detector
- Full behavioral-monitoring platform

### Status
Accepted
```

---

# 94. Product Roadmap

```text
                 LIFE LENS Ω
                      │
             ┌────────┴────────┐
             │                 │
           PHASE 1           PHASE 2
             │                 │
     Job Verification    Trust Graph
             │                 │
     Foreign Offers      Cross-Platform
             │             Verification
             │                 │
             └────────┬────────┘
                      │
                    PHASE 3
                      │
             Trust Trajectory
                      │
              Community Intel
                      │
                    PHASE 4
                      │
          Audio / Video Protection
                      │
                    PHASE 5
                      │
            Unified Trust Platform
```

---

# 95. Industrialization Path

The project's maturity should evolve through measurable gates.

```text
Stage 1
Academic Prototype
        ↓
Stage 2
Working MVP
        ↓
Stage 3
Pilot
        ↓
Stage 4
Validated Product
        ↓
Stage 5
Production System
        ↓
Stage 6
Multi-country Platform
```

Each stage requires real evidence.

---

# 96. Gate Criteria

## Gate 1 — Prototype → MVP

Require:

- End-to-end flow
- Real source integration
- Explainability
- Security baseline
- Test dataset

## Gate 2 — MVP → Pilot

Require:

- Measured precision/recall
- False-positive analysis
- User testing
- Stable integrations
- Privacy review

## Gate 3 — Pilot → Production

Require:

- Operational monitoring
- Incident response
- Source reliability
- Security review
- Data governance
- Model/rule versioning
- Rollback
- Support process

---

# 97. Future Federated Learning

Federated learning remains a future capability, not an MVP dependency.

Before implementing it, prove:

```text
There is enough useful local learning data
+
The learning problem is well-defined
+
Centralized alternatives are insufficient
+
Privacy budget can be justified
+
Model updates can be evaluated safely
```

Do not add federated learning simply because it sounds production-grade.

---

# 98. Future Behavioral Baseline

Before enabling behavioral baselines, require:

```text
Explicit consent
+
minimum sample size
+
baseline confidence
+
poisoning defense
+
user reset
+
privacy review
+
false-positive study
```

---

# 99. Future Video Detection

The system should use a provider abstraction:

```python
class MediaAuthenticityProvider(Protocol):

    def analyze_video(self, media) -> AuthenticityResult:
        ...

    def analyze_audio(self, media) -> AuthenticityResult:
        ...

    def capabilities(self) -> Dict:
        ...
```

This allows providers to be replaced without rewriting LifeLens.

---

# 100. Final Architecture

```text
┌───────────────────────────────────────────────────────────┐
│                 USER INTERFACE                            │
│ Browser Extension / Future Desktop / Mobile             │
└──────────────────────────┬────────────────────────────────┘
                           ▼
┌───────────────────────────────────────────────────────────┐
│                 INPUT NORMALIZATION                       │
│ Entities • Claims • URLs • Contacts • Job Data           │
└──────────────────────────┬────────────────────────────────┘
                           ▼
┌───────────────────────────────────────────────────────────┐
│                 EVIDENCE & VERIFICATION                   │
│ Registry • Website • Domain • Government Sources         │
└──────────────────────────┬────────────────────────────────┘
                           ▼
┌───────────────────────────────────────────────────────────┐
│                    CECT ENGINE                            │
│ Coherence • Evidence Independence • Consistency          │
│ Trajectory                                                │
└──────────────────────────┬────────────────────────────────┘
                           ▼
┌───────────────────────────────────────────────────────────┐
│                 RISK + CONFIDENCE                         │
│ Signals • Reliability • Severity • Uncertainty            │
└──────────────────────────┬────────────────────────────────┘
                           ▼
┌───────────────────────────────────────────────────────────┐
│                EXPLANATION ENGINE                         │
│ Evidence • Findings • Limitations • Safe Verification    │
└──────────────────────────┬────────────────────────────────┘
                           ▼
┌───────────────────────────────────────────────────────────┐
│                 HUMAN DECISION                            │
│ Verify • Continue Carefully • Report • Stop              │
└──────────────────────────┬────────────────────────────────┘
                           ▼
┌───────────────────────────────────────────────────────────┐
│                FEEDBACK / LEARNING                        │
│ Evaluation • Threat Patterns • Future Personal Models    │
└───────────────────────────────────────────────────────────┘
```

---

# 101. The New LifeLens Ω Mental Model

The system should think in this sequence:

```text
WHO?
  ↓
WHAT ARE THEY CLAIMING?
  ↓
WHAT EVIDENCE SUPPORTS IT?
  ↓
IS THAT EVIDENCE INDEPENDENT?
  ↓
DO THE DETAILS AGREE?
  ↓
IS THE INTERACTION ESCALATING?
  ↓
HOW STRONG IS THE EVIDENCE?
  ↓
WHAT IS THE RISK?
  ↓
HOW CONFIDENT ARE WE?
  ↓
WHAT CAN THE USER VERIFY NEXT?
```

---

# 102. Core Innovation

The project should differentiate itself through:

```text
Evidence-grounded verification
        +
Cross-source consistency
        +
Trust trajectory
        +
Explainability
        +
Privacy-aware design
```

The product should not compete primarily on:

```text
"Who has the biggest AI model?"
```

It should compete on:

```text
"Who gives the user the clearest evidence-based
reasoning before they make a high-impact decision?"
```

---

# 103. Final Team Rule

Before adding any feature, ask:

```text
1. Does it solve a real user problem?
2. Is it needed for the current phase?
3. Can we verify that it works?
4. What privacy/security cost does it create?
5. What happens when it is wrong?
6. Does it improve LifeLens's core differentiation?
```

If the answer to most is "no":

> **Do not add the feature yet.**

---

# 104. Final Product Definition

> **LifeLens Ω is a privacy-aware AI trust-verification system that analyzes claims, evidence, identity, consistency, and interaction trajectories to help people verify high-impact digital interactions before they trust, pay, share, or act.**

---

# 105. Phase-1 Definition in One Sentence

> **Build a browser extension that verifies job and foreign employment offers using authoritative sources and evidence-grounded CECT reasoning, then explains the risk and gives the user a safe independent verification path.**

---

# 106. Final Implementation Command for the Team

```text
BUILD FIRST:
    Job Verification

CORE:
    Entity → Claim → Evidence → CECT → Risk → Explanation

PROTECT:
    Privacy + Security + User Control

MEASURE:
    Precision + Recall + False Positives + Latency + User Understanding

DO NOT EXPAND:
    Until the Phase-1 loop works end-to-end.

THEN:
    Cross-Platform Trust Graph
    ↓
    Trust Trajectory
    ↓
    Community Threat Intelligence
    ↓
    Media / Deepfake Protection
```

---

# 107. Success Condition

LifeLens Ω Phase 1 is successful when the team can demonstrate:

```text
A real job posting
        ↓
Real verification source
        ↓
Real claim/evidence graph
        ↓
Real CECT analysis
        ↓
Real risk + confidence
        ↓
Clear explanation
        ↓
User can independently verify the result
```

That is the foundation on which the larger LifeLens Ω vision should be built.
