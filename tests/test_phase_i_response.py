"""
LifeLens Ω — Phase I: Incident Response & Impact Test Suite
Tests for:
1. RDAP Takedown Kit (SSRFShield-safe lookup, P1 wording: "reported as suspected impersonation", P6 human-in-the-loop)
2. Golden-Hour Recovery Flow (3-screen emergency path, bank dispute letter, official portals marked 'confirm current', time-to-complete measured)
3. Campaign Clustering in Trust Graph (infrastructure correlation, 'possibly_related' links only, zero victim data storage)
4. Phase I REST API Endpoints Integration
"""
import pytest
from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.services.response.rdap_takedown import (
    RDAPTakedownService,
    TakedownKit,
    AbuseContacts,
)
from apps.api.app.services.response.golden_hour_recovery import (
    GoldenHourRecoveryService,
    GoldenHourPacket,
)
from apps.api.app.services.response.campaign_clustering import (
    CampaignClusteringService,
    InfrastructureProfile,
    ClusterLink,
    CampaignCluster,
)


client = TestClient(app)


# ── 1. RDAP Takedown Kit Tests ────────────────────────────────────────────────

def test_rdap_takedown_ssrf_safe_lookup():
    """Verify RDAP lookup resolves abuse contacts safely and blocks SSRF targets."""
    service = RDAPTakedownService()

    # 1. Normal domain lookup
    contacts = service.lookup_abuse_contacts("https://fake-job-portal.com/login")
    assert contacts.domain == "fake-job-portal.com"
    assert contacts.registrar_name == "NameCheap, Inc."
    assert "abuse@namecheap.com" in contacts.registrar_abuse_email
    assert "Cloudflare" in contacts.hosting_provider
    assert "abuse@cloudflare.com" in contacts.hosting_abuse_email

    # 2. SSRF Protection: Loopback and metadata IP targets are blocked
    ssrf_target = service.lookup_abuse_contacts("http://169.254.169.254/latest/meta-data")
    assert "BLOCKED" in ssrf_target.registrar_name


def test_takedown_drafts_p1_compliance_and_human_in_the_loop():
    """Verify takedown drafts follow P1 (suspected impersonation, no named accusations) and P6 (manual review)."""
    service = RDAPTakedownService()

    kit = service.generate_takedown_kit(
        domain_or_url="zoom-secure-meeting.org",
        evidence_summary="Deceptive lookalike domain distributing fake client installers",
        victim_contact_email="advocate@verified.org",
    )

    assert kit.is_safe_lookup is True
    drafts = kit.drafts

    # P1: Check wording in registrar draft
    assert "reported as suspected impersonation" in drafts.registrar_draft.lower()
    assert "scammer" not in drafts.registrar_draft.lower()
    assert "fake person" not in drafts.registrar_draft.lower()

    # P6: Human-in-the-loop disclaimer
    assert "Human-in-the-Loop Policy (P6)" in drafts.disclaimer
    assert "never transmits abuse complaints or takedown notices automatically" in drafts.disclaimer


# ── 2. Golden-Hour Recovery Flow Tests ────────────────────────────────────────

def test_golden_hour_flow_three_screens_and_latency_measurement():
    """Verify Golden-Hour recovery generates 3 screens and measures execution time."""
    service = GoldenHourRecoveryService()

    packet = service.execute_golden_hour_flow(
        incident_id="inc_2026_901",
        transaction_id="UPI/428910294821",
        amount=15000.0,
        currency="INR",
        beneficiary_info="fraudulent-merchant@okhdfcbank",
        payment_method="UPI",
        claimed_entity="CBI Investigation Escrow",
    )

    # Latency: Usability measurement in seconds
    assert packet.elapsed_seconds_measured >= 0.0
    assert packet.elapsed_seconds_measured < 1.0  # Extremely fast in-memory execution

    # Screen 1: Bank dispute template
    screen_1 = packet.screen_1_bank_dispute
    assert "Screen 1" in screen_1["title"]
    template = screen_1["dispute_letter_template"]
    assert "UPI/428910294821" in template
    assert "INR 15,000.00" in template
    assert "fraudulent-merchant@okhdfcbank" in template
    assert "Central Bank Fraud Liability Guidelines" in template

    # Screen 2: Evidence Packet
    screen_2 = packet.screen_2_evidence_packet
    assert "Screen 2" in screen_2["title"]
    assert screen_2["evidence_metadata"]["incident_id"] == "inc_2026_901"

    # Screen 3: Official Helplines marked 'confirm current'
    screen_3 = packet.screen_3_official_portals
    assert len(screen_3) >= 4

    india_portal = next(p for p in screen_3 if p["country"] == "India")
    assert india_portal["helpline"] == "1930"
    assert india_portal["url"] == "https://cybercrime.gov.in"
    assert india_portal["url_status"] == "confirm current"

    us_portal = next(p for p in screen_3 if p["country"] == "United States")
    assert us_portal["url_status"] == "confirm current"


# ── 3. Campaign Clustering Tests ──────────────────────────────────────────────

def test_campaign_clustering_infrastructure_links_and_privacy():
    """Verify entities are linked by shared infrastructure, labeled 'possibly_related', with zero victim data."""
    service = CampaignClusteringService()

    # Register technical infrastructure footprints
    service.register_infrastructure_node(InfrastructureProfile(
        entity_domain="phish-auth-zoom.com",
        hosting_asn="AS14061",
        nameservers=["ns1.privacy-names.org", "ns2.privacy-names.org"],
        analytics_id="G-998877",
        tls_cert_serial="04:fa:11:22",
    ))

    service.register_infrastructure_node(InfrastructureProfile(
        entity_domain="fake-meeting-portal.net",
        hosting_asn="AS14061",  # Matches ASN
        nameservers=["ns1.privacy-names.org", "ns2.privacy-names.org"],  # Matches NS
        analytics_id="G-998877",  # Matches Analytics
    ))

    service.register_infrastructure_node(InfrastructureProfile(
        entity_domain="completely-unrelated-blog.org",
        hosting_asn="AS13335",
        nameservers=["ns1.cloudflare.com"],
        analytics_id="G-112233",
    ))

    # Query cluster for target domain
    cluster = service.find_campaign_clusters("phish-auth-zoom.com")
    assert cluster.seed_entity == "phish-auth-zoom.com"
    assert len(cluster.related_entities) == 1

    link = cluster.related_entities[0]
    assert link.related_entity == "fake-meeting-portal.net"
    # Strict Invariant: Must NEVER claim same actor; must be 'possibly_related'
    assert link.relation == "possibly_related"
    assert link.confidence_score >= 0.75
    assert any("AS14061" in s for s in link.shared_indicators)
    assert any("G-998877" in s for s in link.shared_indicators)

    # Privacy Invariant: Zero victim data in the graph
    assert cluster.contains_victim_personal_data is False


# ── 4. Phase I REST API Endpoints Integration ──────────────────────────────────

def test_phase_i_api_endpoints():
    """Verify REST API endpoints for Phase I response & impact tools."""
    # 1. Takedown generator endpoint
    resp_td = client.post(
        "/api/v1/response/takedown/generate",
        json={"domain": "fake-job-portal.com", "evidence_summary": "Credential harvesting"},
    )
    assert resp_td.status_code == 200
    data_td = resp_td.json()
    assert data_td["domain"] == "fake-job-portal.com"
    assert "abuse@namecheap.com" in data_td["abuse_contacts"]["registrar_abuse_email"]
    assert "suspected impersonation" in data_td["drafts"]["registrar_draft"]

    # 2. Golden-Hour start endpoint
    resp_gh = client.post(
        "/api/v1/response/golden-hour/start",
        json={
            "incident_id": "inc_api_123",
            "transaction_id": "UTR_998877",
            "amount": 5000.0,
            "currency": "INR",
            "beneficiary_info": "fake-upi@okhdfc",
        },
    )
    assert resp_gh.status_code == 200
    data_gh = resp_gh.json()
    assert data_gh["incident_id"] == "inc_api_123"
    assert "elapsed_seconds_measured" in data_gh
    assert "UTR_998877" in data_gh["screen_1_bank_dispute"]["dispute_letter_template"]

    # 3. Campaign cluster endpoint
    resp_cl = client.post(
        "/api/v1/response/campaign/cluster",
        json={"target_domain": "isolated-test-domain.com"},
    )
    assert resp_cl.status_code == 200
    assert resp_cl.json()["contains_victim_personal_data"] is False
