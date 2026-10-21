"""
LifeLens Ω — Phase I: Campaign Clustering Service
Links suspicious entities through shared technical infrastructure using the Trust Graph.
Rules:
- Relationship label is strictly "possibly_related"
- NEVER asserts that two entities are the same actor
- NEVER stores victim personal data in the graph (strictly technical infrastructure nodes)
- Every cluster link carries technical provenance and confidence metrics
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set


@dataclass
class InfrastructureProfile:
    entity_domain: str
    hosting_asn: Optional[str] = None
    nameservers: List[str] = field(default_factory=list)
    tls_cert_serial: Optional[str] = None
    tls_issuer: Optional[str] = None
    analytics_id: Optional[str] = None
    registrant_org: Optional[str] = None


@dataclass
class ClusterLink:
    source_entity: str
    related_entity: str
    relation: str = "possibly_related"  # Strictly "possibly_related"; NEVER claims same actor
    confidence_score: float = 0.0
    shared_indicators: List[str] = field(default_factory=list)
    provenance: str = "Technical Infrastructure Graph Correlation"
    caution_note: str = (
        "Shared infrastructure indicates correlated hosting or registrant patterns; "
        "it does not prove identical individual human attribution."
    )


@dataclass
class CampaignCluster:
    cluster_id: str
    seed_entity: str
    related_entities: List[ClusterLink] = field(default_factory=list)
    shared_infrastructure_summary: List[str] = field(default_factory=list)
    contains_victim_personal_data: bool = False  # Must be strictly False


class CampaignClusteringService:
    """
    Correlates external technical observables to uncover syndicated phishing campaigns
    without asserting human attribution or retaining victim credentials.
    """

    def __init__(self) -> None:
        # Technical infrastructure graph node registry (domains -> profiles)
        self._infrastructure_graph: Dict[str, InfrastructureProfile] = {}

    def register_infrastructure_node(self, profile: InfrastructureProfile) -> None:
        """Registers a domain's technical infrastructure footprint in the trust graph."""
        self._infrastructure_graph[profile.entity_domain.lower()] = profile

    def find_campaign_clusters(self, target_domain: str) -> CampaignCluster:
        target = target_domain.lower()
        target_profile = self._infrastructure_graph.get(target)

        if not target_profile:
            return CampaignCluster(
                cluster_id=f"cluster_isolated_{target[:10]}",
                seed_entity=target,
                related_entities=[],
                shared_infrastructure_summary=["No correlated infrastructure registered."],
                contains_victim_personal_data=False,
            )

        related_links: List[ClusterLink] = []
        all_shared_traits: Set[str] = set()

        for domain, profile in self._infrastructure_graph.items():
            if domain == target:
                continue

            shared: List[str] = []

            # 1. ASN Match
            if target_profile.hosting_asn and target_profile.hosting_asn == profile.hosting_asn:
                shared.append(f"Shared Hosting ASN: {profile.hosting_asn}")

            # 2. Nameserver Match
            common_ns = set(target_profile.nameservers) & set(profile.nameservers)
            if common_ns:
                shared.append(f"Shared Nameservers: {', '.join(common_ns)}")

            # 3. Analytics / Tag Manager Match
            if target_profile.analytics_id and target_profile.analytics_id == profile.analytics_id:
                shared.append(f"Shared Analytics / Tag ID: {profile.analytics_id}")

            # 4. TLS Certificate Serial or Common Name Match
            if target_profile.tls_cert_serial and target_profile.tls_cert_serial == profile.tls_cert_serial:
                shared.append(f"Shared TLS Cert Serial: {profile.tls_cert_serial}")

            if shared:
                # Scoring heuristic based on specificity
                score = round(min(0.90, 0.40 + len(shared) * 0.20), 2)
                all_shared_traits.update(shared)

                related_links.append(ClusterLink(
                    source_entity=target,
                    related_entity=domain,
                    relation="possibly_related",
                    confidence_score=score,
                    shared_indicators=shared,
                ))

        cluster_id = f"camp_clust_{target[:8]}" if related_links else f"isolated_{target[:8]}"

        return CampaignCluster(
            cluster_id=cluster_id,
            seed_entity=target,
            related_entities=related_links,
            shared_infrastructure_summary=sorted(list(all_shared_traits)),
            contains_victim_personal_data=False,
        )
