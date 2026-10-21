"""
LifeLens Ω — Phase 6: Post-Incident Recovery Automation API Router
Evolved Blueprint Phase 6 (Months 19-21)

Endpoints:
- POST /api/v1/recovery/assess                    -> Rapid damage assessment
- POST /api/v1/recovery/initiate                  -> Full prioritized recovery plan
- GET  /api/v1/recovery/{recovery_id}             -> Plan status & step progress
- POST /api/v1/recovery/{recovery_id}/step/{id}   -> Toggle step completion
- POST /api/v1/recovery/{recovery_id}/notify      -> Broadcast emergency safety alerts
- GET  /api/v1/recovery/{recovery_id}/report/{agency}          -> JSON complaint packet
- GET  /api/v1/recovery/{recovery_id}/report/{agency}/download -> Formatted text download
"""
from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Response

from apps.api.app.models.recovery import (
    IncidentReport,
    DamageAssessment,
    RecoveryPlan,
    TrustedContact,
    ContactNotificationResult,
    RegulatoryAgency,
    RegulatoryComplaintPacket,
)
from apps.api.app.services.recovery_service import recovery_service

router = APIRouter(prefix="/api/v1/recovery", tags=["phase6-recovery"])


@router.post(
    "/assess",
    response_model=DamageAssessment,
    summary="Assess Damage & Blast Radius",
    description="Calculates severity score, financial exposure, urgency timeframe, and immediate containment directives.",
)
async def assess_incident(incident: IncidentReport) -> DamageAssessment:
    return recovery_service.assess_damage(incident)


@router.post(
    "/initiate",
    response_model=RecoveryPlan,
    summary="Initiate Account & Identity Recovery Workflow",
    description="Generates an ordered, actionable recovery plan with direct security URLs and step completion tracking.",
)
async def initiate_recovery(incident: IncidentReport) -> RecoveryPlan:
    return recovery_service.generate_recovery_plan(incident)


@router.get(
    "/{recovery_id}",
    response_model=RecoveryPlan,
    summary="Fetch Recovery Plan Status",
    description="Retrieves active plan, completed steps count, and current status.",
)
async def get_recovery_status(recovery_id: str) -> RecoveryPlan:
    plan = recovery_service.get_plan(recovery_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Recovery plan '{recovery_id}' not found.")
    return plan


@router.post(
    "/{recovery_id}/step/{step_id}/complete",
    response_model=RecoveryPlan,
    summary="Mark Recovery Step Complete / Incomplete",
    description="Toggles the completion status of a specific recovery step and recalculates progress.",
)
async def toggle_step_completion(
    recovery_id: str,
    step_id: str,
    completed: bool = Query(True, description="True to check off step, False to uncheck"),
) -> RecoveryPlan:
    plan = recovery_service.complete_step(recovery_id, step_id, completed)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Recovery plan '{recovery_id}' not found.")
    return plan


@router.post(
    "/{recovery_id}/notify-contacts",
    response_model=List[ContactNotificationResult],
    summary="Broadcast Emergency Alerts to Trusted Contacts",
    description="Dispatches safety warnings to trusted peers/family without leaking confidential credentials.",
)
async def notify_contacts(
    recovery_id: str, contacts: List[TrustedContact]
) -> List[ContactNotificationResult]:
    plan = recovery_service.get_plan(recovery_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Recovery plan '{recovery_id}' not found.")
    return recovery_service.notify_trusted_contacts(recovery_id, contacts)


@router.get(
    "/{recovery_id}/regulatory-report/{agency}",
    response_model=RegulatoryComplaintPacket,
    summary="Generate Regulatory / Law Enforcement Complaint Packet",
    description="Pre-fills official complaints for FBI IC3, FTC, Action Fraud UK, or NCRP India with cryptographic audit hashes.",
)
async def generate_regulatory_complaint(
    recovery_id: str, agency: RegulatoryAgency
) -> RegulatoryComplaintPacket:
    plan = recovery_service.get_plan(recovery_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Recovery plan '{recovery_id}' not found.")
    return recovery_service.generate_regulatory_report(recovery_id, agency)


@router.get(
    "/{recovery_id}/regulatory-report/{agency}/download",
    summary="Download Plain-Text Regulatory Complaint File",
    description="Returns pre-formatted text file ready for copy-pasting into government reporting portals.",
)
async def download_complaint_file(
    recovery_id: str, agency: RegulatoryAgency
) -> Response:
    plan = recovery_service.get_plan(recovery_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Recovery plan '{recovery_id}' not found.")
    packet = recovery_service.generate_regulatory_report(recovery_id, agency)
    filename = f"LifeLens_Complaint_{agency.value}_{recovery_id}.txt"
    return Response(
        content=packet.formatted_complaint_text,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
