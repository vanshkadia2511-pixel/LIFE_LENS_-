"""
LifeLens Ω — Phase I: Incident Response & Impact API Router
Exposes:
- Takedown Kit generation (RDAP abuse lookup & P1 compliant drafts)
- Golden-Hour 3-step recovery packet ("I Just Paid")
- Campaign clustering (infrastructure graph correlation)
"""
from __future__ import annotations
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from apps.api.app.services.response.rdap_takedown import RDAPTakedownService
from apps.api.app.services.response.golden_hour_recovery import GoldenHourRecoveryService
from apps.api.app.services.response.campaign_clustering import (
    CampaignClusteringService,
    InfrastructureProfile,
)

router = APIRouter(prefix="/api/v1/response", tags=["Phase I Response & Recovery"])

_takedown_service = RDAPTakedownService()
_golden_hour_service = GoldenHourRecoveryService()
_clustering_service = CampaignClusteringService()


# ── Schemas ───────────────────────────────────────────────────────────────────

class TakedownRequest(BaseModel):
    domain: str = Field(..., description="Target domain or link to generate abuse drafts for")
    evidence_summary: str = Field("Suspected impersonation and fraudulent lures", description="Summary of observed evidence")
    victim_contact_email: Optional[str] = Field(None, description="Optional victim or reporter contact email")

class GoldenHourRequest(BaseModel):
    incident_id: str
    transaction_id: str
    amount: float
    currency: str = "INR"
    beneficiary_info: str
    payment_method: str = "UPI"
    claimed_entity: str = "Unknown Entity"

class ClusterQueryRequest(BaseModel):
    target_domain: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/takedown/generate")
async def generate_takedown_kit(req: TakedownRequest):
    """
    Looks up registrar and hosting abuse contacts via RDAP (SSRFShield-safe)
    and prepares editable takedown drafts (P1 & P6 compliant).
    """
    res = _takedown_service.generate_takedown_kit(
        domain_or_url=req.domain,
        evidence_summary=req.evidence_summary,
        victim_contact_email=req.victim_contact_email,
    )
    return {
        "domain": res.domain,
        "abuse_contacts": {
            "registrar_name": res.abuse_contacts.registrar_name,
            "registrar_abuse_email": res.abuse_contacts.registrar_abuse_email,
            "registrar_abuse_phone": res.abuse_contacts.registrar_abuse_phone,
            "hosting_provider": res.abuse_contacts.hosting_provider,
            "hosting_abuse_email": res.abuse_contacts.hosting_abuse_email,
        },
        "drafts": {
            "registrar_draft": res.drafts.registrar_draft,
            "hosting_draft": res.drafts.hosting_draft,
            "platform_draft": res.drafts.platform_draft,
            "disclaimer": res.drafts.disclaimer,
        },
        "is_safe_lookup": res.is_safe_lookup,
    }


@router.post("/golden-hour/start")
async def start_golden_hour_recovery(req: GoldenHourRequest):
    """
    Executes the 3-step Golden Hour recovery flow and measures completion latency.
    """
    packet = _golden_hour_service.execute_golden_hour_flow(
        incident_id=req.incident_id,
        transaction_id=req.transaction_id,
        amount=req.amount,
        currency=req.currency,
        beneficiary_info=req.beneficiary_info,
        payment_method=req.payment_method,
        claimed_entity=req.claimed_entity,
    )
    return {
        "incident_id": packet.incident_id,
        "elapsed_seconds_measured": packet.elapsed_seconds_measured,
        "screen_1_bank_dispute": packet.screen_1_bank_dispute,
        "screen_2_evidence_packet": packet.screen_2_evidence_packet,
        "screen_3_official_portals": packet.screen_3_official_portals,
        "disclaimer": packet.disclaimer,
    }


@router.post("/campaign/cluster")
async def find_campaign_clusters(req: ClusterQueryRequest):
    """
    Correlates target domain against known technical infrastructure in the trust graph.
    All links are labeled strictly 'possibly_related'. Zero victim data stored.
    """
    cluster = _clustering_service.find_campaign_clusters(req.target_domain)
    return {
        "cluster_id": cluster.cluster_id,
        "seed_entity": cluster.seed_entity,
        "related_entities": [
            {
                "related_entity": r.related_entity,
                "relation": r.relation,
                "confidence_score": r.confidence_score,
                "shared_indicators": r.shared_indicators,
                "provenance": r.provenance,
                "caution_note": r.caution_note,
            }
            for r in cluster.related_entities
        ],
        "shared_infrastructure_summary": cluster.shared_infrastructure_summary,
        "contains_victim_personal_data": cluster.contains_victim_personal_data,
    }
