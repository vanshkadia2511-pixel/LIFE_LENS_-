"""
LifeLens Ω — Phase C: Desktop Call Guard Service
Platform-agnostic local Call Guardian (Layers 2, 3, 4, Receipt)

Guarantees:
- Zero persisted media (audio, video, screenshots never hit disk/DB)
- Ephemeral in-memory ring-buffer for live transcript processing
- Layer 2 live transcript trajectory engine (7 triggers, < 3.0s latency)
- Layer 3 Out-of-band verification interstitial & cooling-off timer
- Layer 4 Liveness challenge coach (coaches challenges without claiming automated pass/fail)
- Post-call receipt & ledger logging with transcript discard policy
"""
from __future__ import annotations
import re
import time
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging

from apps.api.app.models.desktop_guard import (
    DesktopGuardStartRequest,
    DesktopGuardSessionState,
    DesktopGuardChunkRequest,
    DesktopGuardAlert,
    DesktopSignalType,
    VerificationInterstitial,
    CallbackChecklistItem,
    LivenessChallenge,
    DesktopGuardEndRequest,
    PostCallReceipt,
)

logger = logging.getLogger(__name__)

# Trigger pattern definitions for Layer 2
_TRIGGER_PATTERNS = {
    DesktopSignalType.SIG_CALL_TRANSFER_REQUEST: [
        re.compile(r"\b(?:transfer|wire|send)\b.*?(?:wire|funds|money|\$|usd|inr|pounds|euro|account)", re.IGNORECASE),
        re.compile(r"\b(?:transfer|wire)\s+\$?\d+.*?(?:immediately|today|now)\b", re.IGNORECASE),
    ],
    DesktopSignalType.SIG_CALL_SECRECY_DEMAND: [
        re.compile(r"\b(?:don'?t|do\s+not)\s+tell\s+anyone\b", re.IGNORECASE),
        re.compile(r"\bkeep\s+this\s+(?:between\s+us|strictly\s+confidential|confidential)\b", re.IGNORECASE),
        re.compile(r"\bdo\s+not\s+consult\s+(?:your\s+)?(?:family|bank|lawyer|police)\b", re.IGNORECASE),
    ],
    DesktopSignalType.SIG_CALL_URGENCY_PRESSURE: [
        re.compile(r"\b(?:within\s+\d+\s+minutes?|act\s+right\s+now)\b", re.IGNORECASE),
        re.compile(r"\bright\s+now\s+or\s+(?:you\s+will\s+face|immediate\s+legal)\b", re.IGNORECASE),
        re.compile(r"\b(?:do\s+not\s+disconnect|if\s+you\s+hang\s+up).*?(?:arrest|warrant)\b", re.IGNORECASE),
    ],
    DesktopSignalType.SIG_CALL_CREDENTIAL_REQUEST: [
        re.compile(r"\b(?:read|send|tell|give|share)\b.*?(?:otp|password|pin|cvv|2fa|verification\s+code)", re.IGNORECASE),
        re.compile(r"\b(?:netbanking\s+password|login\s+credentials?)\b", re.IGNORECASE),
    ],
    DesktopSignalType.SIG_REMOTE_ACCESS_REQUEST: [
        re.compile(r"\b(?:download|install|open)\s+(?:and\s+install\s+)?(?:anydesk|teamviewer|quicksupport|ultraviewer)\b", re.IGNORECASE),
        re.compile(r"\b(?:screen\s+share|remote\s+access)\b.*?(?:inspect|fix|camera|device)", re.IGNORECASE),
    ],
    DesktopSignalType.SIG_OFFICIAL_IMPERSONATION: [
        re.compile(r"\b(?:digital\s+arrest)\b", re.IGNORECASE),
        re.compile(r"\bofficer\b.*?(?:cbi|police|cyber|narcotics|customs|enforcement)", re.IGNORECASE),
        re.compile(r"\barrest\s+warrant\b.*?(?:issued|in\s+your\s+name)", re.IGNORECASE),
    ],
    DesktopSignalType.SIG_PAYMENT_DETAILS: [
        re.compile(r"\b(?:upi\s+id|[a-zA-Z0-9.\-_]+@(okhdfcbank|okaxis|ybl|paytm|oksbi))\b", re.IGNORECASE),
        re.compile(r"\b(?:bitcoin|btc|eth|crypto)\s+(?:address|wallet)\b|[13][a-km-zA-HJ-NP-Z1-9]{25,34}|0x[a-fA-F0-9]{40}", re.IGNORECASE),
        re.compile(r"\bgift\s+cards?\b.*?(?:google\s+play|apple|steam|amazon)", re.IGNORECASE),
    ],
}


@dataclass
class _InternalSession:
    session_id: str
    platform: str
    is_active: bool
    started_at: datetime
    transcript_buffer: List[str] = field(default_factory=list)
    alerts: List[DesktopGuardAlert] = field(default_factory=list)
    interstitial: Optional[VerificationInterstitial] = None
    checklist_status: Dict[int, bool] = field(default_factory=dict)


class DesktopCallGuardService:
    """
    In-memory local service orchestrating Desktop Call Guard sessions.
    Strictly zero persistence of raw audio/video or unconsented transcripts.
    """

    def __init__(self):
        self._sessions: Dict[str, _InternalSession] = {}

    def start_session(self, req: DesktopGuardStartRequest) -> DesktopGuardSessionState:
        session_id = f"ds_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        if not req.consent_flag:
            return DesktopGuardSessionState(
                session_id=session_id,
                is_active=False,
                guard_indicator="GUARD_OFF",
                platform=req.platform,
                started_at=now.isoformat(),
                status_message="User consent must be explicitly granted before starting Desktop Call Guard (§P5, §P6).",
                active_interstitial=False,
            )

        sess = _InternalSession(
            session_id=session_id,
            platform=req.platform,
            is_active=True,
            started_at=now,
        )
        self._sessions[session_id] = sess

        return DesktopGuardSessionState(
            session_id=session_id,
            is_active=True,
            guard_indicator="GUARD_ON",
            platform=req.platform,
            started_at=now.isoformat(),
            status_message="Desktop Call Guard is ON and actively monitoring transcript stream locally.",
            active_interstitial=False,
        )

    def ingest_transcript_chunk(self, req: DesktopGuardChunkRequest) -> List[DesktopGuardAlert]:
        sess = self._sessions.get(req.session_id)
        if not sess or not sess.is_active:
            return []

        t_start = time.perf_counter()
        # Ephemeral buffer (max 100 entries ring-buffer)
        sess.transcript_buffer.append(req.transcript_text)
        if len(sess.transcript_buffer) > 100:
            sess.transcript_buffer.pop(0)

        fired_alerts: List[DesktopGuardAlert] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        # Evaluate against Layer 2 trajectory triggers
        for sig_type, patterns in _TRIGGER_PATTERNS.items():
            matched = False
            for pat in patterns:
                m = pat.search(req.transcript_text)
                if m:
                    matched = True
                    trigger_phrase = m.group(0)
                    break

            if matched:
                latency_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
                alert = DesktopGuardAlert(
                    alert_id=f"alt_{uuid.uuid4().hex[:8]}",
                    session_id=req.session_id,
                    signal_type=sig_type,
                    severity="HIGH",
                    trigger_phrase=trigger_phrase,
                    detected_at=now_iso,
                    latency_ms=latency_ms,
                    description=f"Layer 2 trajectory trigger: {sig_type.value}",
                    recommended_action="Pause call immediately and perform out-of-band verification (§P6).",
                )
                sess.alerts.append(alert)
                fired_alerts.append(alert)

                # High-risk trigger spawns Layer 3 Interstitial if none active
                if not sess.interstitial:
                    sess.interstitial = self._create_interstitial(req.session_id)

        return fired_alerts

    def _create_interstitial(self, session_id: str) -> VerificationInterstitial:
        now_iso = datetime.now(timezone.utc).isoformat()
        checklist = [
            CallbackChecklistItem(
                step_id=0,
                title="Pause and Mute",
                instruction="Mute your microphone or tell caller you will call back through official directory.",
                completed=False,
            ),
            CallbackChecklistItem(
                step_id=1,
                title="Independent Callback Directory",
                instruction="Look up official phone number from trusted portal/card (NOT any number provided on this call).",
                completed=False,
            ),
            CallbackChecklistItem(
                step_id=2,
                title="Code Word & Identity Challenge",
                instruction="Challenge the caller with pre-agreed code word or confirm request via official email.",
                completed=False,
            ),
        ]
        return VerificationInterstitial(
            interstitial_id=f"int_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            requires_pause=True,
            headline="PAUSE: High-risk request detected. Do NOT pay, transfer money, or share credentials.",
            cooling_off_minutes=15,
            callback_checklist=checklist,
            suggested_code_word="SHIELD-2026-ALPHA",
            created_at=now_iso,
        )

    def get_active_interstitial(self, session_id: str) -> Optional[VerificationInterstitial]:
        sess = self._sessions.get(session_id)
        if not sess:
            return None
        return sess.interstitial

    def complete_verification_step(self, session_id: str, step_index: int) -> Any:
        sess = self._sessions.get(session_id)
        if not sess or not sess.interstitial:
            return None

        if 0 <= step_index < len(sess.interstitial.callback_checklist):
            sess.interstitial.callback_checklist[step_index].completed = True
            sess.checklist_status[step_index] = True

        return sess

    def get_liveness_challenges(self, session_id: str) -> List[LivenessChallenge]:
        """
        Layer 4 Liveness Challenge Coach.
        Suggests challenges to expose deepfakes, but NEVER claims an automated pass/fail verdict (P6).
        """
        return [
            LivenessChallenge(
                challenge_id="ch_profile_yaw",
                action_instruction="Turn your head slowly 90 degrees to profile and hold for 2 seconds.",
                rationale="2D face-swap masks and diffusion pipelines warp or clip at extreme yaw angles.",
                evaluation_guidance="User observes reaction: Does the ear or jawline blur or disappear?",
                automated_verdict_claimed=False,
            ),
            LivenessChallenge(
                challenge_id="ch_hand_occlusion",
                action_instruction="Pass your open hand slowly across your mouth and nose.",
                rationale="Facial occlusions disrupt neural boundary landmarks, causing avatar flickering.",
                evaluation_guidance="User observes reaction: Does the hand distort through the face or mask peel?",
                automated_verdict_claimed=False,
            ),
            LivenessChallenge(
                challenge_id="ch_physical_object",
                action_instruction="Hold up a physical object (e.g. pen, key, notebook) next to your cheek.",
                rationale="Synthetic models struggle to composite foreign non-facial objects in real-time.",
                evaluation_guidance="User observes reaction: Does the object boundary blend into skin texture?",
                automated_verdict_claimed=False,
            ),
            LivenessChallenge(
                challenge_id="ch_random_phrase",
                action_instruction="Repeat a random unpredictable phrase (e.g. 'purple flamingo in green forest').",
                rationale="Voice cloning and TTS pipelines incur 2-4 second processing lag or robotic cadence.",
                evaluation_guidance="User observes reaction: Is there noticeable audio-video desync or unnatural delay?",
                automated_verdict_claimed=False,
            ),
        ]

    def end_session(self, req: DesktopGuardEndRequest) -> PostCallReceipt:
        sess = self._sessions.get(req.session_id)
        if not sess:
            # Fallback receipt for missing session
            return PostCallReceipt(
                receipt_id=f"rcp_{uuid.uuid4().hex[:10]}",
                session_id=req.session_id,
                platform="unknown",
                duration_seconds=0,
                signals_fired=[],
                requests_detected=[],
                verification_steps_completed=[],
                ledger_entry_hash="0x" + hashlib.sha256(b"empty").hexdigest(),
                transcript_retained=False,
            )

        sess.is_active = False
        duration_sec = int((datetime.now(timezone.utc) - sess.started_at).total_seconds())

        # Collect detected request types
        req_types = list(set([a.signal_type.value for a in sess.alerts]))

        # Collect completed verification checklist steps
        completed_steps = []
        if sess.interstitial:
            for step in sess.interstitial.callback_checklist:
                if step.completed:
                    completed_steps.append(step.title)

        # Zero persistence policy: discard transcript unless explicitly requested
        transcript_retained = bool(req.opt_in_retain_transcript)
        if not transcript_retained:
            sess.transcript_buffer.clear()

        # Compute cryptographic ledger entry hash (§P3 Provenance)
        ledger_payload = (
            f"{sess.session_id}|{sess.platform}|{duration_sec}|"
            f"{','.join(req_types)}|{','.join(completed_steps)}|{transcript_retained}"
        )
        ledger_hash = "0x" + hashlib.sha256(ledger_payload.encode("utf-8")).hexdigest()

        return PostCallReceipt(
            receipt_id=f"rcp_{uuid.uuid4().hex[:10]}",
            session_id=sess.session_id,
            platform=sess.platform,
            duration_seconds=max(1, duration_sec),
            signals_fired=sess.alerts,
            requests_detected=req_types,
            verification_steps_completed=completed_steps,
            ledger_entry_hash=ledger_hash,
            transcript_retained=transcript_retained,
        )

    def get_session(self, session_id: str) -> Optional[_InternalSession]:
        return self._sessions.get(session_id)
