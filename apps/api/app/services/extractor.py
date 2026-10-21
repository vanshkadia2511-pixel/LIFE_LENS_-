"""
LifeLens Ω — Claim Extractor
Implementation Plan §28–29, §58

Extracts structured claims from a VerificationRequest.
Extraction confidence: HIGH | MEDIUM | LOW (§58)

NOTE: Phase 1 uses rules + structured extraction (§7 AI/NLP stack).
Low-confidence extraction is visible to the reasoning engine (§58).
"""
from __future__ import annotations
import re
from typing import List, Tuple
from datetime import datetime, timezone
import uuid

from ..models.request import VerificationRequest
from ..models.claim import Claim, ClaimType
from ..models.entity import Entity


# ---------------------------------------------------------------------------
# Extraction confidence (§58)
# ---------------------------------------------------------------------------

class ExtractionConfidence:
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ---------------------------------------------------------------------------
# Patterns for claim extraction (§28)
# ---------------------------------------------------------------------------

# Urgency patterns
_URGENCY_PATTERNS = [
    r"\bimmediate(ly)?\b", r"\bwithin\s+\d+\s+days?\b", r"\bjoin\s+now\b",
    r"\bnot\s+miss\b", r"\bdeadline\b", r"\bfinal\s+date\b", r"\blast\s+chance\b",
    r"\bapply\s+today\b", r"\blimited\s+time\b", r"\bact\s+fast\b",
]

# Payment / fee patterns
_PAYMENT_PATTERNS = [
    r"\bprocessing\s+fee\b", r"\bregistration\s+fee\b", r"\bsecurity\s+deposit\b",
    r"\brefundable\s+(?:training\s+)?deposit\b", r"\btraining\s+(?:fee|deposit)\b",
    r"\bbackground\s+check\s+fee\b", r"\bvisa\s+fee\b", r"\bsend\s+money\b",
    r"\btransfer\s+funds\b", r"\bwire\s+transfer\b", r"\bpay\s+upfront\b",
    r"\badvance\s+payment\b", r"\bmandatory\s+contribution\b",
    r"\bcompliance\s+transfer\b", r"\bhardware\s+(?:bond|deposit|fee)\b",
    r"\bequipment\s+(?:bond|deposit|fee)\b", r"\bonboarding\s+(?:fee|deposit|transfer)\b",
    r"\b(?:transfer|deposit|payment)\s+of\s+[\$£€¥]?\d+\b",
]

# Document request patterns
_DOCUMENT_PATTERNS = [
    r"\bpassport\s+(copy|scan|photo|number)\b", r"\bnational\s+id\b",
    r"\bbank\s+(details|account|statement)\b", r"\bsocial\s+security\b",
    r"\btax\s+(id|number|form)\b", r"\bpersonal\s+id\b", r"\bcredit\s+card\b",
]

# Visa claim patterns
_VISA_PATTERNS = [
    r"\bvisa\s+(sponsored|sponsorship|provided|included|guaranteed|arranged)\b",
    r"\bwork\s+(permit|authorization|visa)\b", r"\bimmigration\s+support\b",
]

# Off-platform patterns
_OFF_PLATFORM_PATTERNS = [
    r"\bwhatsapp\b", r"\btelegram\b", r"\bsignal\b",
    r"\bemail\s+me\s+directly\b", r"\bcontact\s+me\s+at\b", r"\btext\s+me\b",
]

# No-experience patterns
_NO_EXPERIENCE_PATTERNS = [
    r"\bno\s+experience\s+(required|needed|necessary)\b",
    r"\bfreshers?\s+welcome\b", r"\btraining\s+provided\b",
    r"\bno\s+qualification\s+required\b",
]


def _check_patterns(text: str, patterns: List[str]) -> Tuple[bool, str]:
    """Return (matched, matched_text)."""
    text_lower = text.lower()
    for pattern in patterns:
        m = re.search(pattern, text_lower)
        if m:
            return True, m.group(0)
    return False, ""


def _extract_salary(text: str) -> Tuple[bool, str]:
    """Extract salary claim from text."""
    pattern = r"(?:salary|pay|compensation|package)[:\s]+([^\n.]{3,60})"
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        return True, m.group(1).strip()
    # fallback: currency amounts
    m = re.search(r"[\$£€₹]\s*[\d,]+(?:\s*-\s*[\$£€₹]?\s*[\d,]+)?", text)
    if m:
        return True, m.group(0).strip()
    return False, ""


def _extract_location(text: str, claimed_location: str | None) -> Tuple[bool, str]:
    """Extract location claim, preferring explicitly claimed location."""
    if claimed_location:
        return True, claimed_location
    # Rough extraction: "in <Country/City>"
    m = re.search(r"\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", text)
    if m:
        return True, m.group(1)
    return False, ""


# ---------------------------------------------------------------------------
# Main extractor
# ---------------------------------------------------------------------------

class ClaimExtractor:
    """
    Phase 1 claim extractor.
    Uses rules + structured extraction per §7 (Phase 1 AI/NLP stack).
    """

    VERSION = "0.1.0"

    def extract(
        self, request: VerificationRequest, entity: Entity
    ) -> List[Claim]:
        """
        Extract all claims from a VerificationRequest for the given entity.
        Returns a list of Claim objects with extraction confidence in claim_text prefix.
        """
        claims: List[Claim] = []
        text = " ".join(filter(None, [
            request.job_title,
            request.job_description,
            request.company_name,
            request.company_website,
            request.recruiter_email,
        ]))

        now = datetime.now(timezone.utc)

        # --- LOCATION claim (§28) ---
        found, value = _extract_location(text, request.claimed_location)
        if found:
            claims.append(Claim(
                claim_id=str(uuid.uuid4()),
                entity_id=entity.entity_id,
                claim_text=f"Location claimed: {value}",
                claim_type=ClaimType.LOCATION,
                source="job_posting",
                confidence=0.8 if request.claimed_location else 0.4,
                first_observed_at=now,
                last_observed_at=now,
            ))

        # --- VISA claim (§28) ---
        found, value = _check_patterns(text, _VISA_PATTERNS)
        if found:
            claims.append(Claim(
                claim_id=str(uuid.uuid4()),
                entity_id=entity.entity_id,
                claim_text=f"Visa/work authorization claimed: '{value}'",
                claim_type=ClaimType.VISA,
                source="job_posting",
                confidence=0.9,
                first_observed_at=now,
                last_observed_at=now,
            ))

        # --- SALARY claim (§28) ---
        found, value = _extract_salary(text)
        if found:
            claims.append(Claim(
                claim_id=str(uuid.uuid4()),
                entity_id=entity.entity_id,
                claim_text=f"Salary claimed: {value}",
                claim_type=ClaimType.SALARY,
                source="job_posting",
                confidence=0.7,
                first_observed_at=now,
                last_observed_at=now,
            ))

        # --- URGENCY claim (§28) ---
        found, value = _check_patterns(text, _URGENCY_PATTERNS)
        if found:
            claims.append(Claim(
                claim_id=str(uuid.uuid4()),
                entity_id=entity.entity_id,
                claim_text=f"Urgency pressure detected: '{value}'",
                claim_type=ClaimType.URGENCY,
                source="job_posting",
                confidence=0.85,
                first_observed_at=now,
                last_observed_at=now,
            ))

        # --- PAYMENT claim (§28) ---
        found, value = _check_patterns(text, _PAYMENT_PATTERNS)
        if found:
            claims.append(Claim(
                claim_id=str(uuid.uuid4()),
                entity_id=entity.entity_id,
                claim_text=f"Payment or fee requested: '{value}'",
                claim_type=ClaimType.PAYMENT,
                source="job_posting",
                confidence=0.95,
                first_observed_at=now,
                last_observed_at=now,
            ))

        # --- DOCUMENT request (§28) ---
        found, value = _check_patterns(text, _DOCUMENT_PATTERNS)
        if found:
            claims.append(Claim(
                claim_id=str(uuid.uuid4()),
                entity_id=entity.entity_id,
                claim_text=f"Sensitive document requested: '{value}'",
                claim_type=ClaimType.DOCUMENT,
                source="job_posting",
                confidence=0.9,
                first_observed_at=now,
                last_observed_at=now,
            ))

        # --- CONTACT / off-platform (§28) ---
        found, value = _check_patterns(text, _OFF_PLATFORM_PATTERNS)
        if found:
            claims.append(Claim(
                claim_id=str(uuid.uuid4()),
                entity_id=entity.entity_id,
                claim_text=f"Off-platform contact requested: '{value}'",
                claim_type=ClaimType.CONTACT,
                source="job_posting",
                confidence=0.8,
                first_observed_at=now,
                last_observed_at=now,
            ))

        # --- WEBSITE claim (recruiter email domain) ---
        if request.recruiter_email and "@" in request.recruiter_email:
            domain = request.recruiter_email.split("@")[-1].lower()
            claims.append(Claim(
                claim_id=str(uuid.uuid4()),
                entity_id=entity.entity_id,
                claim_text=f"Recruiter email domain: {domain}",
                claim_type=ClaimType.CONTACT,
                source="recruiter_email",
                confidence=1.0,
                first_observed_at=now,
                last_observed_at=now,
            ))

        return claims

    def extract_claims(
        self, request: VerificationRequest, entity: Entity
    ) -> List[Claim]:
        """Alias for extract method."""
        return self.extract(request, entity)

    def extract_entities(
        self, request: VerificationRequest
    ) -> List[Entity]:
        """
        Extract Entity models from the incoming request (§10, §28).
        """
        entities: List[Entity] = []

        # 1. Company entity
        if request.company_name or request.company_website:
            entities.append(Entity(
                entity_id=f"ent-company-{uuid.uuid4().hex[:8]}",
                entity_type="COMPANY",
                claimed_name=request.company_name,
                claimed_role="Employer",
                website=request.company_website,
                normalized_name=request.company_name.lower().strip() if request.company_name else None,
            ))

        # 2. Recruiter entity
        if request.recruiter_name or request.recruiter_email or request.recruiter_phone:
            entities.append(Entity(
                entity_id=f"ent-recruiter-{uuid.uuid4().hex[:8]}",
                entity_type="RECRUITER",
                claimed_name=request.recruiter_name,
                claimed_role="Recruiter",
                email=request.recruiter_email,
                phone=request.recruiter_phone,
                normalized_name=request.recruiter_name.lower().strip() if request.recruiter_name else None,
            ))

        if not entities:
            # Default placeholder entity if none explicitly provided
            entities.append(Entity(
                entity_id=f"ent-unknown-{uuid.uuid4().hex[:8]}",
                entity_type="COMPANY",
                claimed_name="Unknown Employer",
            ))

        return entities

