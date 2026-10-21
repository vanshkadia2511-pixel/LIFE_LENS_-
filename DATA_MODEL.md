# LifeLens Ω — Canonical Data Model

**Document Version:** 2.0  
**Implements:** Implementation Plan §9, §10, §11, §12, §13, §15, §18, §21, §92  

---

## 1. Core Model Hierarchy

The entire LifeLens Ω reasoning system is grounded in the formal relationship between **Entities**, **Claims**, and **Evidence**:

```text
       ┌───────────────────────────────┐
       │      VerificationRequest      │
       └──────────────┬────────────────┘
                      │ extracts
         ┌────────────┴────────────┐
         ▼                         ▼
   ┌───────────┐             ┌───────────┐
   │  Entity   │             │   Claim   │
   └─────┬─────┘             └─────┬─────┘
         │                         │
         │ matched against         │ supported/refuted by
         ▼                         ▼
   ┌─────────────────────────────────────┐
   │              Evidence               │
   └──────────────────┬──────────────────┘
                      │ fed into
                      ▼
   ┌─────────────────────────────────────┐
   │           CECTAssessment            │
   │  (Coherence, Independence,          │
   │   Consistency, Trajectory)          │
   └──────────────────┬──────────────────┘
                      │ produces
                      ▼
   ┌─────────────────────────────────────┐
   │        RiskAssessmentResult         │
   │    (RiskLevel, RiskScore, Conf.)    │
   └──────────────────┬──────────────────┘
                      │ explains to user
                      ▼
   ┌─────────────────────────────────────┐
   │          ExplanationReport          │
   └─────────────────────────────────────┘
```

---

## 2. Model Specifications

### 2.1 VerificationRequest (§9.1)
```python
@dataclass
class VerificationRequest:
    request_id: str
    created_at: Optional[datetime]
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None
    recruiter_phone: Optional[str] = None
    claimed_country: Optional[str] = "GB"
    claimed_location: Optional[str] = None
    job_description: Optional[str] = None
    source_platform: str = "BROWSER_EXTENSION"
    consent_for_analysis: bool = True
```

### 2.2 Entity (§10)
```python
class VerificationStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    VERIFIED = "VERIFIED"
    CONTRADICTED = "CONTRADICTED"
    UNAVAILABLE = "UNAVAILABLE"

@dataclass
class Entity:
    entity_id: str
    entity_type: str  # COMPANY | RECRUITER | DOMAIN
    claimed_name: Optional[str] = None
    claimed_role: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    normalized_name: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.UNKNOWN
    verification_confidence: float = 0.0
    source_references: List[str] = field(default_factory=list)
```

### 2.3 Claim (§11)
```python
class ClaimType(str, Enum):
    IDENTITY = "IDENTITY"
    EMPLOYMENT = "EMPLOYMENT"
    AUTHORITY = "AUTHORITY"
    LOCATION = "LOCATION"
    SALARY = "SALARY"
    VISA = "VISA"
    RECRUITMENT = "RECRUITMENT"
    PAYMENT = "PAYMENT"
    DOCUMENT = "DOCUMENT"
    URGENCY = "URGENCY"
    CONTACT = "CONTACT"
    WEBSITE = "WEBSITE"

@dataclass
class Claim:
    claim_id: str
    entity_id: str
    claim_text: str
    claim_type: ClaimType
    source: str
    supporting_evidence_ids: List[str] = field(default_factory=list)
    contradicting_evidence_ids: List[str] = field(default_factory=list)
    verification_status: VerificationStatus = VerificationStatus.UNKNOWN
    confidence: float = 0.0
```

### 2.4 Evidence (§12, §13)
```python
class SourceStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    STALE = "STALE"
    CONFLICTING = "CONFLICTING"
    NOT_APPLICABLE = "NOT_APPLICABLE"

@dataclass
class Evidence:
    evidence_id: str
    source_type: str        # BUSINESS_REGISTRY | DOMAIN_REGISTRY | OFFICIAL_WEBSITE | etc.
    source_name: str        # Companies House | UAE NER | DNS MX
    observed_value: str
    captured_at: datetime
    source_authority: float       # 0.0 to 1.0 (Government registry = 0.95+)
    source_independence: float    # 0.0 to 1.0 (Independent = 0.90+, Claimant = 0.10)
    user_verifiable: bool
    verification_path: Optional[str]
    evidence_strength: float
    source_status: SourceStatus
```

### 2.5 LedgerBlock (Phase 5 §100)
```python
@dataclass
class LedgerBlock:
    index: int
    timestamp: str
    request_id: str
    entity_name: str
    risk_level: str
    confidence: float
    evidence_hashes: List[str]
    previous_hash: str
    block_hash: str
```
