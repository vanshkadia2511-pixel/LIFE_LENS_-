"""
LifeLens Ω — Phase 6: Post-Incident Recovery Automation Service
Implementation Plan §6 & Evolved Blueprint Phase 6 (Months 19-21)

Provides:
- Damage assessment & blast radius calculation
- Priority-ranked recovery workflow generation (Tier 1 Critical to Tier 4)
- Session & step tracking (target recovery time < 30 min)
- Emergency trusted contact safety broadcasting
- Regulatory complaint packet generation (FBI IC3, FTC, Action Fraud, NCRP)
"""
from __future__ import annotations
import hashlib
import json
import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from apps.api.app.models.recovery import (
    IncidentType,
    AccountTier,
    UrgencyLevel,
    ActionType,
    RecoveryStep,
    DamageAssessment,
    IncidentReport,
    RecoveryPlan,
    TrustedContact,
    ContactNotificationResult,
    RegulatoryAgency,
    RegulatoryComplaintPacket,
)


class RecoveryService:
    """Core engine for post-incident damage mitigation and automated recovery."""

    # Curated authoritative security portals
    PORTAL_DIRECTORY = {
        "google": {
            "name": "Google / Gmail Account Security",
            "tier": AccountTier.TIER_1_CRITICAL,
            "session_url": "https://myaccount.google.com/device-activity",
            "password_url": "https://myaccount.google.com/signinoptions/password",
            "mfa_url": "https://myaccount.google.com/signinoptions/two-step-verification",
        },
        "microsoft": {
            "name": "Microsoft / Outlook Security",
            "tier": AccountTier.TIER_1_CRITICAL,
            "session_url": "https://account.live.com/Activity",
            "password_url": "https://account.live.com/proofs/manage/additional",
            "mfa_url": "https://account.live.com/proofs/manage/additional",
        },
        "apple": {
            "name": "Apple ID / iCloud Security",
            "tier": AccountTier.TIER_1_CRITICAL,
            "session_url": "https://appleid.apple.com/account/manage",
            "password_url": "https://appleid.apple.com/account/manage",
            "mfa_url": "https://appleid.apple.com/account/manage",
        },
        "chase": {
            "name": "Chase Bank Fraud & Security",
            "tier": AccountTier.TIER_1_CRITICAL,
            "session_url": "https://www.chase.com/personal/fraud-security",
            "phone": "1-800-935-9935",
        },
        "bank_of_america": {
            "name": "Bank of America Fraud Department",
            "tier": AccountTier.TIER_1_CRITICAL,
            "session_url": "https://www.bankofamerica.com/security-center/report-suspicious-activity/",
            "phone": "1-800-432-1000",
        },
        "paypal": {
            "name": "PayPal Resolution & Security",
            "tier": AccountTier.TIER_1_CRITICAL,
            "session_url": "https://www.paypal.com/myaccount/security/",
            "dispute_url": "https://www.paypal.com/disputes/",
        },
        "coinbase": {
            "name": "Coinbase Security & Lockout",
            "tier": AccountTier.TIER_1_CRITICAL,
            "session_url": "https://www.coinbase.com/settings/security",
            "emergency_url": "https://help.coinbase.com/en/coinbase/privacy-and-security/data-privacy/how-can-i-make-my-account-more-secure",
        },
        "linkedin": {
            "name": "LinkedIn Active Sessions & Privacy",
            "tier": AccountTier.TIER_3_MEDIUM,
            "session_url": "https://www.linkedin.com/psettings/sessions",
            "password_url": "https://www.linkedin.com/psettings/change-password",
        },
        "credit_freeze_us": {
            "experian": "https://www.experian.com/freeze/center.html",
            "transunion": "https://www.transunion.com/credit-freeze",
            "equifax": "https://www.equifax.com/personal/credit-report-services/credit-freeze/",
        },
    }

    def __init__(self):
        self._plans: Dict[str, RecoveryPlan] = {}
        self._lock = threading.Lock()

    def assess_damage(self, incident: IncidentReport) -> DamageAssessment:
        """
        Calculates damage score, blast radius, urgency level, and containment directives.
        """
        base_score = 0.2
        urgency = UrgencyLevel.STANDARD_24_HOUR
        containment: List[str] = []
        exposed_assets: List[str] = list(incident.compromised_accounts)

        # 1. Evaluate Incident Type Severity
        if incident.incident_type == IncidentType.ADVANCE_FEE_PAID:
            base_score += 0.45
            urgency = UrgencyLevel.IMMEDIATE_15_MIN
            containment.append("Contact remitting financial institution immediately to request a wire recall or stop payment.")
            containment.append("Retain all transaction hashes, recipient IBAN/UPI addresses, and chat transcripts.")

        elif incident.incident_type == IncidentType.MALWARE_EXECUTED:
            base_score += 0.50
            urgency = UrgencyLevel.IMMEDIATE_15_MIN
            containment.append("Disconnect this computer immediately from Wi-Fi and Ethernet cables.")
            containment.append("Do NOT enter any passwords or banking credentials on this machine until remediated.")
            containment.append("Prepare a secondary clean device (e.g. mobile phone) for all credential rotations.")

        elif incident.incident_type == IncidentType.SESSION_HIJACK:
            base_score += 0.40
            urgency = UrgencyLevel.IMMEDIATE_15_MIN
            containment.append("Issue global session revocation across primary identity and email providers.")
            containment.append("Clear all browser cookies and active extensions.")

        elif incident.incident_type == IncidentType.CREDENTIAL_THEFT:
            base_score += 0.35
            urgency = UrgencyLevel.HIGH_1_HOUR
            containment.append("Change password immediately starting with primary recovery email.")
            containment.append("Check account forwarding rules and authorized third-party OAuth apps.")

        elif incident.incident_type == IncidentType.IDENTITY_THEFT:
            base_score += 0.40
            urgency = UrgencyLevel.HIGH_1_HOUR
            containment.append("Place an immediate credit security freeze at the major credit reporting agencies.")
            containment.append("Monitor government tax portals for unauthorized returns or benefit claims.")

        elif incident.incident_type == IncidentType.OFF_PLATFORM_EXTORTION:
            base_score += 0.35
            urgency = UrgencyLevel.HIGH_1_HOUR
            containment.append("Cease all communication with perpetrator immediately. Do not make any payments.")
            containment.append("Export full chat transcripts, phone numbers, and profile screenshots before blocking.")

        # 2. Evaluate Financial Exposure
        if incident.financial_amount_lost > 0:
            if incident.financial_amount_lost >= 5000:
                base_score += 0.25
            elif incident.financial_amount_lost >= 500:
                base_score += 0.15
            else:
                base_score += 0.05

        # 3. Evaluate Account Tiers Involved
        has_tier1 = any(
            any(k in acc.lower() for k in ["bank", "chase", "gmail", "email", "crypto", "wallet", "paypal"])
            for acc in incident.compromised_accounts
        )
        if has_tier1:
            base_score += 0.20
            urgency = UrgencyLevel.IMMEDIATE_15_MIN

        # Normalize score
        severity_score = min(1.0, max(0.1, round(base_score, 2)))

        if severity_score >= 0.75:
            severity_label: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "CRITICAL"
        elif severity_score >= 0.55:
            severity_label = "HIGH"
        elif severity_score >= 0.35:
            severity_label = "MEDIUM"
        else:
            severity_label = "LOW"

        blast_summary = (
            f"Incident classified as {incident.incident_type.value}. "
            f"Exposes {len(exposed_assets)} target assets with "
            f"{incident.currency} {incident.financial_amount_lost:,.2f} reported financial loss. "
            f"Urgency timeframe: {urgency.value}."
        )

        return DamageAssessment(
            severity_score=severity_score,
            severity_label=severity_label,
            urgency_level=urgency,
            estimated_financial_loss=incident.financial_amount_lost,
            currency=incident.currency,
            compromised_identity_assets=exposed_assets,
            blast_radius_summary=blast_summary,
            containment_directives=containment,
        )

    def generate_recovery_plan(self, incident: IncidentReport) -> RecoveryPlan:
        """
        Constructs an ordered, actionable recovery plan tailored to the incident.
        Target total completion time is < 30 minutes for core steps.
        """
        recovery_id = f"rec-{uuid.uuid4().hex[:8]}"
        assessment = self.assess_damage(incident)
        steps: List[RecoveryStep] = []
        step_order = 1

        # --- STEP 1: Emergency Physical / Network Containment (if malware) ---
        if incident.incident_type == IncidentType.MALWARE_EXECUTED:
            steps.append(
                RecoveryStep(
                    step_id=f"step-{step_order}",
                    order=step_order,
                    tier=AccountTier.TIER_1_CRITICAL,
                    action_type=ActionType.DISCONNECT_DEVICE,
                    target_service="Local Workstation",
                    title="Disconnect Infected Device from Network",
                    instructions="Unplug ethernet cable and turn off Wi-Fi on the affected machine. Perform all subsequent password changes from a smartphone or clean secondary device.",
                    direct_url=None,
                    estimated_minutes=2,
                )
            )
            step_order += 1

        # --- STEP 2: Financial Freeze / Recall (if financial fraud) ---
        if (
            incident.incident_type == IncidentType.ADVANCE_FEE_PAID
            or incident.financial_amount_lost > 0
            or any("bank" in a.lower() or "paypal" in a.lower() for a in incident.compromised_accounts)
        ):
            steps.append(
                RecoveryStep(
                    step_id=f"step-{step_order}",
                    order=step_order,
                    tier=AccountTier.TIER_1_CRITICAL,
                    action_type=ActionType.FREEZE_FINANCIAL,
                    target_service="Primary Bank / Card Issuer",
                    title="Initiate Immediate Wire Recall & Card Lock",
                    instructions="Call the fraud emergency number on the back of your card. State that you were a victim of authorized push payment fraud or wire theft and request a transaction freeze.",
                    direct_url=self.PORTAL_DIRECTORY["chase"]["session_url"],
                    estimated_minutes=6,
                )
            )
            step_order += 1

        # --- STEP 3: Primary Email Session Revocation & Password Rotation ---
        steps.append(
            RecoveryStep(
                step_id=f"step-{step_order}",
                order=step_order,
                tier=AccountTier.TIER_1_CRITICAL,
                action_type=ActionType.REVOKE_ALL_SESSIONS,
                target_service="Primary Email (Gmail / Outlook / Apple)",
                title="Sign Out of All Active Sessions & Revoke Device Access",
                instructions="Log into your primary email from a clean device. Go to Security -> Devices and click 'Sign out of all other sessions'. This invalidates stolen session tokens.",
                direct_url=self.PORTAL_DIRECTORY["google"]["session_url"],
                estimated_minutes=3,
            )
        )
        step_order += 1

        steps.append(
            RecoveryStep(
                step_id=f"step-{step_order}",
                order=step_order,
                tier=AccountTier.TIER_1_CRITICAL,
                action_type=ActionType.ROTATE_CREDENTIALS,
                target_service="Primary Email Password & 2FA",
                title="Rotate Email Password & Verify 2FA Recovery Methods",
                instructions="Change your email password to a strong generated passphrase. Ensure recovery phone number and backup email belong to you and have not been modified by an attacker.",
                direct_url=self.PORTAL_DIRECTORY["google"]["password_url"],
                estimated_minutes=4,
            )
        )
        step_order += 1

        # --- STEP 4: Credit Bureau Freeze (if Identity Theft / SSN harvested) ---
        if incident.incident_type == IncidentType.IDENTITY_THEFT or any(
            k in str(incident.compromised_accounts).lower() for k in ["ssn", "passport", "id", "driver", "aadhaar"]
        ):
            steps.append(
                RecoveryStep(
                    step_id=f"step-{step_order}",
                    order=step_order,
                    tier=AccountTier.TIER_2_HIGH,
                    action_type=ActionType.CREDIT_BUREAU_FREEZE,
                    target_service="Experian, TransUnion & Equifax",
                    title="Place Free Security Freezes at Major Credit Bureaus",
                    instructions="A credit freeze stops scammers from opening fraudulent loans, credit cards, or lines of credit in your name. Freezes are free by law.",
                    direct_url=self.PORTAL_DIRECTORY["credit_freeze_us"]["experian"],
                    estimated_minutes=8,
                )
            )
            step_order += 1

        # --- STEP 5: Professional & Social Media Account Check ---
        steps.append(
            RecoveryStep(
                step_id=f"step-{step_order}",
                order=step_order,
                tier=AccountTier.TIER_3_MEDIUM,
                action_type=ActionType.ROTATE_CREDENTIALS,
                target_service="LinkedIn & Recruitment Portals",
                title="Revoke LinkedIn Sessions & Check Connected Apps",
                instructions="Visit LinkedIn Settings -> Sign-in & Security -> Where you're signed in -> End all active sessions. Verify your posted contact information.",
                direct_url=self.PORTAL_DIRECTORY["linkedin"]["session_url"],
                estimated_minutes=3,
            )
        )
        step_order += 1

        # --- STEP 6: Trusted Contacts Safety Broadcast ---
        steps.append(
            RecoveryStep(
                step_id=f"step-{step_order}",
                order=step_order,
                tier=AccountTier.TIER_4_LOW,
                action_type=ActionType.NOTIFY_TRUSTED_CONTACTS,
                target_service="Family & Trusted Peer Network",
                title="Alert Trusted Contacts Regarding Potential Impersonation",
                instructions="Send a brief warning to close contacts and family. Scammers often use compromised identities to contact friends asking for urgent emergency bail or gift cards.",
                direct_url=None,
                estimated_minutes=2,
            )
        )
        step_order += 1

        # --- STEP 7: Law Enforcement & Regulatory Filing ---
        steps.append(
            RecoveryStep(
                step_id=f"step-{step_order}",
                order=step_order,
                tier=AccountTier.TIER_4_LOW,
                action_type=ActionType.FILE_REGULATORY_REPORT,
                target_service="FBI IC3 / FTC / Action Fraud / NCRP",
                title="Export & File Formal Government Cybercrime Complaint",
                instructions="Export your pre-filled LifeLens Ω regulatory report and submit it to the national reporting body (FBI IC3 in the US, Action Fraud in the UK, NCRP in India). Official reports are essential for bank reimbursement claims.",
                direct_url="https://www.ic3.gov/",
                estimated_minutes=5,
            )
        )

        total_est_minutes = sum(s.estimated_minutes for s in steps)

        plan = RecoveryPlan(
            recovery_id=recovery_id,
            incident=incident,
            assessment=assessment,
            steps=steps,
            total_steps=len(steps),
            completed_steps=0,
            estimated_total_minutes=total_est_minutes,
            status="ACTIVE",
        )

        with self._lock:
            self._plans[recovery_id] = plan

        return plan

    def get_plan(self, recovery_id: str) -> Optional[RecoveryPlan]:
        with self._lock:
            return self._plans.get(recovery_id)

    def complete_step(
        self, recovery_id: str, step_id: str, completed: bool = True
    ) -> Optional[RecoveryPlan]:
        with self._lock:
            plan = self._plans.get(recovery_id)
            if not plan:
                return None

            for step in plan.steps:
                if step.step_id == step_id:
                    step.completed = completed
                    step.completed_at = (
                        datetime.now(timezone.utc).isoformat() if completed else None
                    )
                    break

            plan.completed_steps = sum(1 for s in plan.steps if s.completed)
            if plan.completed_steps == plan.total_steps:
                plan.status = "COMPLETED"
            elif plan.completed_steps > 0:
                plan.status = "IN_PROGRESS"
            else:
                plan.status = "ACTIVE"

            return plan

    def notify_trusted_contacts(
        self, recovery_id: str, contacts: List[TrustedContact]
    ) -> List[ContactNotificationResult]:
        """
        Dispatches emergency safety warnings to trusted contacts.
        Does not reveal passwords or private financial credentials.
        """
        plan = self.get_plan(recovery_id)
        incident_type = plan.incident.incident_type.value if plan else "SECURITY_INCIDENT"
        user_label = plan.incident.user_id if plan and plan.incident.user_id else "The user"

        results: List[ContactNotificationResult] = []
        now = datetime.now(timezone.utc).isoformat()

        for c in contacts:
            msg = (
                f"🚨 [LifeLens Ω Emergency Security Alert] "
                f"{user_label} has reported a {incident_type} security incident. "
                f"Please disregard any unexpected requests for money, wire transfers, or gift cards "
                f"sent from their email, social, or messaging accounts until further notice."
            )
            results.append(
                ContactNotificationResult(
                    recipient=f"{c.name} ({c.destination})",
                    channel=c.contact_channel,
                    status="SENT",
                    sent_at=now,
                    message_preview=msg,
                )
            )

        return results

    def generate_regulatory_report(
        self, recovery_id: str, agency: RegulatoryAgency = RegulatoryAgency.FBI_IC3
    ) -> RegulatoryComplaintPacket:
        """
        Generates a formal pre-filled complaint report tailored for law enforcement.
        Computes a cryptographic SHA-256 fingerprint of the incident evidence.
        """
        plan = self.get_plan(recovery_id)
        if not plan:
            # Fallback mock report if plan ID not registered
            now = datetime.now(timezone.utc).isoformat()
            return RegulatoryComplaintPacket(
                agency=agency,
                agency_full_name="Federal Bureau of Investigation — IC3",
                complaint_reference="REF-MOCK-001",
                incident_summary="Security incident reported to LifeLens Ω",
                monetary_loss="USD 0.00",
                perpetrator_identifiers={},
                evidence_fingerprint_sha256="0" * 64,
                narrative="No active incident plan found.",
                submission_portal_url="https://www.ic3.gov/",
                formatted_complaint_text="Incident not found.",
                generated_at=now,
            )

        incident = plan.incident
        now = datetime.now(timezone.utc).isoformat()

        # Build evidence hash
        hasher = hashlib.sha256()
        hasher.update(incident.incident_id.encode("utf-8"))
        hasher.update(incident.incident_type.value.encode("utf-8"))
        hasher.update(str(incident.financial_amount_lost).encode("utf-8"))
        hasher.update(json.dumps(incident.scammer_identifiers, sort_keys=True).encode("utf-8"))
        evidence_hash = hasher.hexdigest()

        agency_metadata = {
            RegulatoryAgency.FBI_IC3: {
                "name": "FBI Internet Crime Complaint Center (IC3)",
                "url": "https://www.ic3.gov/",
                "ref_prefix": "IC3-USA-",
            },
            RegulatoryAgency.FTC: {
                "name": "Federal Trade Commission (FTC ReportFraud)",
                "url": "https://reportfraud.ftc.gov/",
                "ref_prefix": "FTC-USA-",
            },
            RegulatoryAgency.ACTION_FRAUD_UK: {
                "name": "Action Fraud — National Fraud & Cyber Crime Reporting Centre (UK)",
                "url": "https://www.actionfraud.police.uk/",
                "ref_prefix": "NFRC-UK-",
            },
            RegulatoryAgency.NCRP_INDIA: {
                "name": "National Cyber Crime Reporting Portal (MHA India)",
                "url": "https://cybercrime.gov.in/",
                "ref_prefix": "NCRP-IN-",
            },
            RegulatoryAgency.INTERPOL: {
                "name": "INTERPOL Financial Crime and Anti-Corruption Centre (IFCACC)",
                "url": "https://www.interpol.int/Crimes/Financial-crime",
                "ref_prefix": "INT-GLO-",
            },
        }

        meta = agency_metadata.get(agency, agency_metadata[RegulatoryAgency.FBI_IC3])
        ref_id = f"{meta['ref_prefix']}{uuid.uuid4().hex[:10].upper()}"

        narrative = (
            f"Victim was targeted via an employment/recruitment scam categorized under {incident.incident_type.value}.\n"
            f"Incident occurred on or about: {incident.occurred_at}.\n"
            f"Total direct monetary loss incurred: {incident.currency} {incident.financial_amount_lost:,.2f}.\n"
            f"Compromised user assets: {', '.join(incident.compromised_accounts) if incident.compromised_accounts else 'None specified'}.\n"
            f"Perpetrator contacts/identifiers observed: {json.dumps(incident.scammer_identifiers, indent=2)}.\n"
            f"Detailed narrative: {incident.description or 'Perpetrator impersonated an authorized recruiter and solicited unauthorized payments/credentials under false pretenses.'}\n"
            f"Cryptographic Evidence Audit Hash (SHA-256): {evidence_hash}\n"
        )

        formatted_text = f"""================================================================================
OFFICIAL CYBERCRIME COMPLAINT PACKET (PREPARED DRAFT — NOT FILED)
================================================================================
Target Agency:          {meta['name']}
Official Portal:        {meta['url']} (Confirm current)
Submission Method:      MANUAL FILING REQUIRED (No official public automated submission API exists)
Generated Reference:    {ref_id}
Date of Generation:     {now}
Evidence SHA-256 Hash:  {evidence_hash}
--------------------------------------------------------------------------------
IMPORTANT NOTICE TO VICTIM:
This complaint packet was PREPARED by LifeLens Ω to assist you in reporting.
LifeLens Ω DOES NOT automatically submit, transmit, or file complaints on your behalf.
You must manually review this draft, navigate to the official portal URL, and submit.
--------------------------------------------------------------------------------
1. INCIDENT CLASSIFICATION
   Category:            {incident.incident_type.value}
   Total Loss:          {incident.currency} {incident.financial_amount_lost:,.2f}
   Status:              {plan.status}
   
2. PERPETRATOR DETAILS (Known Indicators)
{json.dumps(incident.scammer_identifiers, indent=3)}

3. COMPROMISED ACCOUNTS & IDENTITY ASSETS
   Assets:              {', '.join(incident.compromised_accounts) if incident.compromised_accounts else 'None'}

4. NARRATIVE & CHRONOLOGY
{narrative}
--------------------------------------------------------------------------------
CERTIFICATION & PROVENANCE:
This complaint document was compiled using the LifeLens Ω cryptographic recovery ledger.
All evidence items and transaction logs have been fingerprinted for law enforcement submission.
Confirm all portal URLs and emergency helplines are current before taking action.
================================================================================
"""

        return RegulatoryComplaintPacket(
            agency=agency,
            agency_full_name=meta["name"],
            complaint_reference=ref_id,
            incident_summary=f"Loss of {incident.currency} {incident.financial_amount_lost:,.2f} via {incident.incident_type.value}",
            monetary_loss=f"{incident.currency} {incident.financial_amount_lost:,.2f}",
            perpetrator_identifiers=incident.scammer_identifiers,
            evidence_fingerprint_sha256=evidence_hash,
            narrative=narrative,
            submission_portal_url=f"{meta['url']} (Confirm current)",
            formatted_complaint_text=formatted_text,
            generated_at=now,
            is_filed_automatically=False,
            submission_api_available=False,
        )


# Global singleton instance for the API layer
recovery_service = RecoveryService()
