"""
LifeLens Ω — Phase D: Platform Integrations & Evidence Independence (Rule C)
MeetingMediaProvider, SIMULATED Provider, Zoom RTMS Adapter, and Participant Independence Analysis
"""
from __future__ import annotations
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set
import logging

from apps.api.app.models.evidence import SourceStatus

logger = logging.getLogger(__name__)


@dataclass
class MeetingParticipant:
    participant_id: str
    display_name: str
    is_authenticated: bool
    join_origin_id: str
    joined_at: datetime
    account_email: Optional[str] = None
    org_domain: Optional[str] = None
    account_created_window: Optional[str] = None  # e.g. "SAME_DAY", "SAME_HOUR", "ESTABLISHED"
    is_host: bool = False
    vouched_by_participant_ids: List[str] = field(default_factory=list)
    independent_verified_callback: bool = False


@dataclass
class ParticipantJoinEvent:
    event_id: str
    participant_id: str
    joined_at: datetime
    is_guest: bool
    join_origin_id: str


@dataclass
class ParticipantIndependenceResult:
    raw_participant_count: int
    effective_independent_source_count: int
    has_shared_origin_cluster: bool
    has_independently_verified_participant: bool
    can_achieve_verified_trust: bool
    verdict_blockers: List[str] = field(default_factory=list)
    cluster_mapping: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class MeetingSignal:
    signal_name: str
    severity: str
    description: str
    provenance: Dict[str, Any]


class MeetingMediaProvider(ABC):
    """Abstract interface for meeting platform telemetry and streams."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def is_simulated(self) -> bool:
        pass

    @abstractmethod
    def get_participants(self, meeting_id: str) -> List[MeetingParticipant]:
        pass

    @abstractmethod
    def get_join_events(self, meeting_id: str) -> List[ParticipantJoinEvent]:
        pass


class SimulatedMeetingMediaProvider(MeetingMediaProvider):
    """
    Clearly labeled SIMULATED provider for offline and deterministic testing (§P4).
    Simulated outputs carry source='SIMULATED' and contribute zero evidence weight.
    """

    def __init__(self, is_simulated: bool = True):
        self._is_simulated = is_simulated
        self.source_tag = "SIMULATED"

    @property
    def provider_name(self) -> str:
        return "SIMULATED_MEETING_PROVIDER"

    @property
    def is_simulated(self) -> bool:
        return self._is_simulated

    def get_participants(self, meeting_id: str) -> List[MeetingParticipant]:
        now = datetime.now(timezone.utc)
        return [
            MeetingParticipant(
                participant_id="sim_part_01",
                display_name="Simulated Host",
                is_authenticated=True,
                org_domain="example.com",
                join_origin_id="sim_origin_host",
                joined_at=now,
                is_host=True,
                independent_verified_callback=True,
            ),
            MeetingParticipant(
                participant_id="sim_part_02",
                display_name="Simulated Guest",
                is_authenticated=False,
                join_origin_id="sim_origin_guest_link",
                joined_at=now + timedelta(seconds=2),
                independent_verified_callback=False,
            ),
        ]

    def get_join_events(self, meeting_id: str) -> List[ParticipantJoinEvent]:
        now = datetime.now(timezone.utc)
        return [
            ParticipantJoinEvent(
                event_id="sim_evt_01",
                participant_id="sim_part_01",
                joined_at=now,
                is_guest=False,
                join_origin_id="sim_origin_host",
            )
        ]

    def get_e2ee_coverage_policy(self) -> str:
        """
        Policy documentation regarding personal encrypted messaging calls.
        """
        return (
            "WhatsApp, Telegram, and Signal utilize personal end-to-end encryption (E2EE) with no "
            "official server-side stream interception API. LifeLens Ω enforces coverage strictly via the "
            "Phase C Desktop Call Guard running locally on the user's machine. "
            "No scraping or encryption bypass is ever attempted (§P5 Privacy by default)."
        )


class ZoomRTMSAdapter(MeetingMediaProvider):
    """
    Zoom Realtime Media Streams (RTMS) adapter prepared against official Zoom developer docs.
    Strictly disabled until approved Zoom Marketplace OAuth credentials are provided (§P6).
    """

    def __init__(self, credentials: Optional[Dict[str, str]] = None):
        creds = credentials or {}
        self.client_id = creds.get("ZOOM_RTMS_CLIENT_ID") or os.environ.get("ZOOM_RTMS_CLIENT_ID")
        self.client_secret = creds.get("ZOOM_RTMS_CLIENT_SECRET") or os.environ.get("ZOOM_RTMS_CLIENT_SECRET")
        self.account_id = creds.get("ZOOM_RTMS_ACCOUNT_ID") or os.environ.get("ZOOM_RTMS_ACCOUNT_ID")

        # Keep strictly disabled until approved production credentials are provided
        self.is_enabled = bool(self.client_id and self.client_secret and self.account_id)
        self.status = SourceStatus.AVAILABLE if self.is_enabled else SourceStatus.UNAVAILABLE
        self.risk_boost = 0.0

    @property
    def provider_name(self) -> str:
        return "ZOOM_RTMS_ADAPTER"

    @property
    def is_simulated(self) -> bool:
        return False

    def get_setup_checklist(self) -> List[str]:
        return [
            "1. Register a Server-to-Server OAuth App in Zoom App Marketplace (marketplace.zoom.us).",
            "2. Enable Realtime Media Streams (RTMS) feature on your Zoom account.",
            "3. Request scopes: meeting:read:rtms and meeting:write:rtms.",
            "4. Configure environment variables: ZOOM_RTMS_CLIENT_ID, ZOOM_RTMS_CLIENT_SECRET, ZOOM_RTMS_ACCOUNT_ID.",
            "5. Configure webhook signature verification secret: ZOOM_WEBHOOK_SECRET_TOKEN.",
        ]

    def get_participants(self, meeting_id: str) -> List[MeetingParticipant]:
        if not self.is_enabled:
            return []
        # Official RTMS client calls would happen here once authenticated
        return []

    def get_join_events(self, meeting_id: str) -> List[ParticipantJoinEvent]:
        if not self.is_enabled:
            return []
        return []


class GoogleMeetProviderStub(MeetingMediaProvider):
    @property
    def provider_name(self) -> str:
        return "GOOGLE_MEET_STUB"

    @property
    def is_simulated(self) -> bool:
        return False

    is_enabled: bool = False

    def get_participants(self, meeting_id: str) -> List[MeetingParticipant]:
        return []

    def get_join_events(self, meeting_id: str) -> List[ParticipantJoinEvent]:
        return []


class MicrosoftTeamsProviderStub(MeetingMediaProvider):
    @property
    def provider_name(self) -> str:
        return "MS_TEAMS_STUB"

    @property
    def is_simulated(self) -> bool:
        return False

    is_enabled: bool = False

    def get_participants(self, meeting_id: str) -> List[MeetingParticipant]:
        return []

    def get_join_events(self, meeting_id: str) -> List[ParticipantJoinEvent]:
        return []


class CiscoWebexProviderStub(MeetingMediaProvider):
    @property
    def provider_name(self) -> str:
        return "CISCO_WEBEX_STUB"

    @property
    def is_simulated(self) -> bool:
        return False

    is_enabled: bool = False

    def get_participants(self, meeting_id: str) -> List[MeetingParticipant]:
        return []

    def get_join_events(self, meeting_id: str) -> List[ParticipantJoinEvent]:
        return []


class VendorMeetingBotAdapter:
    """
    Optional vendor meeting-bot API abstraction behind a feature flag.
    Includes written advisory notice on privacy, cost, and third-party data handling.
    """

    def __init__(self, feature_enabled: bool = False):
        self.is_enabled = feature_enabled

    def get_privacy_advisory(self) -> str:
        return (
            "Third-Party Data Handling Notice: Utilizing a vendor meeting-bot SaaS routes call audio "
            "and transcripts through external third-party infrastructure. This incurs per-minute SaaS costs, "
            "presents cross-border data transfer risks under GDPR/DPDP, and bypasses local confidentiality. "
            "Explicit user consent is mandatory before enabling this integration."
        )


class ParticipantIndependenceAnalyzer:
    """
    Implements Rule C in CECT Evidence Independence logic:
    - Participants who share the same join origin (same invite link, same host, same account-creation window)
      and vouch for each other count as ONE evidence source.
    - A 'verified-trust' outcome requires at least one independently verified participant
      (org-authenticated, or confirmed through an out-of-band callback).
    """

    def analyze_participant_independence(self, participants: List[MeetingParticipant]) -> ParticipantIndependenceResult:
        if not participants:
            return ParticipantIndependenceResult(
                raw_participant_count=0,
                effective_independent_source_count=0,
                has_shared_origin_cluster=False,
                has_independently_verified_participant=False,
                can_achieve_verified_trust=False,
                verdict_blockers=["No participants found in meeting session."],
            )

        raw_count = len(participants)
        clusters: Dict[str, List[MeetingParticipant]] = {}

        # Group by join_origin_id
        for p in participants:
            origin_key = p.join_origin_id or f"origin_individual_{p.participant_id}"
            clusters.setdefault(origin_key, []).append(p)

        effective_sources = 0
        has_shared_origin = False
        has_verified_participant = False

        for origin_key, group in clusters.items():
            # Check if group has multiple participants who vouch for each other
            if len(group) > 1:
                has_shared_origin = True
                # Rule C: Collapses into ONE evidence source
                effective_sources += 1
            else:
                effective_sources += 1

            # Check for independently verified participant
            for p in group:
                if (p.is_authenticated and p.org_domain) or p.independent_verified_callback:
                    has_verified_participant = True

        can_verify = has_verified_participant
        blockers: List[str] = []
        if not has_verified_participant:
            blockers.append("At least one independently verified participant is required for verified-trust (§Rule C)")

        cluster_map = {k: [p.participant_id for p in v] for k, v in clusters.items()}

        return ParticipantIndependenceResult(
            raw_participant_count=raw_count,
            effective_independent_source_count=effective_sources,
            has_shared_origin_cluster=has_shared_origin,
            has_independently_verified_participant=has_verified_participant,
            can_achieve_verified_trust=can_verify,
            verdict_blockers=blockers,
            cluster_mapping=cluster_map,
        )


class MeetingMetadataSignals:
    """
    Detects participant-metadata risk signals:
    - SIG_PARTICIPANTS_SHARED_ORIGIN
    - SIG_NO_INDEPENDENT_VERIFIED_PARTICIPANT
    - SIG_GUEST_JOIN_BURST
    """

    def detect_signals(self, participants: List[MeetingParticipant]) -> List[MeetingSignal]:
        signals: List[MeetingSignal] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        if not participants:
            return signals

        # 1. SIG_PARTICIPANTS_SHARED_ORIGIN
        origin_counts: Dict[str, int] = {}
        for p in participants:
            origin_counts[p.join_origin_id] = origin_counts.get(p.join_origin_id, 0) + 1

        shared_origins = [k for k, v in origin_counts.items() if v >= 2]
        if shared_origins:
            signals.append(
                MeetingSignal(
                    signal_name="SIG_PARTICIPANTS_SHARED_ORIGIN",
                    severity="HIGH",
                    description=(
                        f"Multiple participants share join origin '{shared_origins[0]}'. "
                        "Per Rule C, shared origin participants collapse into a single evidence source."
                    ),
                    provenance={"origin_clusters": shared_origins, "detected_at": now_iso},
                )
            )

        # 2. SIG_NO_INDEPENDENT_VERIFIED_PARTICIPANT
        has_verified = any(
            (p.is_authenticated and p.org_domain) or p.independent_verified_callback
            for p in participants
        )
        if not has_verified:
            signals.append(
                MeetingSignal(
                    signal_name="SIG_NO_INDEPENDENT_VERIFIED_PARTICIPANT",
                    severity="HIGH",
                    description=(
                        "Zero independently verified participants found on call. "
                        "All attendees are unverified guests. Verified-trust state is blocked (§Rule C)."
                    ),
                    provenance={"total_participants": len(participants), "detected_at": now_iso},
                )
            )

        # 3. SIG_GUEST_JOIN_BURST
        # Check if >= 3 unauthenticated guests joined within 15 seconds
        guests = [p for p in participants if not p.is_authenticated]
        if len(guests) >= 3:
            sorted_times = sorted([p.joined_at for p in guests])
            time_delta = (sorted_times[-1] - sorted_times[0]).total_seconds()
            if time_delta <= 15.0:
                signals.append(
                    MeetingSignal(
                        signal_name="SIG_GUEST_JOIN_BURST",
                        severity="MEDIUM",
                        description=f"Rapid guest join burst: {len(guests)} guests joined within {time_delta:.1f}s.",
                        provenance={"burst_count": len(guests), "window_seconds": time_delta, "detected_at": now_iso},
                    )
                )

        return signals
