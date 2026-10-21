"""
LifeLens Ω — Cross-Platform Trust Graph Service (Phase 2)
Implementation Plan §81

Links recruiters, company entities, email domains, and historic verification outcomes
into an in-memory / persistent trust graph for relationship analysis.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class TrustNode:
    node_id: str
    node_type: str  # COMPANY | RECRUITER | DOMAIN | PHONE | WEBSITE
    name: str
    attributes: dict = field(default_factory=dict)
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    verification_count: int = 0
    scam_flags: int = 0


@dataclass
class TrustEdge:
    source_id: str
    target_id: str
    relation: str  # OPERATES_FROM | RECRUITS_FOR | USES_DOMAIN | CLAIMS_IDENTITY
    confidence: float = 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TrustGraphService:
    """
    Phase 2 Entity & Identity Trust Graph (§81).
    Tracks nodes (Companies, Recruiters, Domains) and directed edges (RECRUITS_FOR, OPERATES_FROM).
    Computes node trust scores based on past verification trajectories.
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, TrustNode] = {}
        self._edges: List[TrustEdge] = []

    def get_or_create_node(self, node_id: str, node_type: str, name: str, attributes: Optional[dict] = None) -> TrustNode:
        if node_id not in self._nodes:
            self._nodes[node_id] = TrustNode(
                node_id=node_id,
                node_type=node_type,
                name=name,
                attributes=attributes or {},
            )
        return self._nodes[node_id]

    def add_edge(self, source_id: str, target_id: str, relation: str, confidence: float = 1.0) -> TrustEdge:
        edge = TrustEdge(
            source_id=source_id,
            target_id=target_id,
            relation=relation,
            confidence=confidence,
        )
        self._edges.append(edge)
        return edge

    def record_verification(
        self,
        company_name: str,
        recruiter_email: Optional[str] = None,
        domain: Optional[str] = None,
        is_risky: bool = False,
    ) -> dict:
        comp_id = f"company:{company_name.lower().strip()}"
        comp_node = self.get_or_create_node(comp_id, "COMPANY", company_name)
        comp_node.verification_count += 1
        if is_risky:
            comp_node.scam_flags += 1

        rec_node = None
        if recruiter_email:
            rec_id = f"recruiter:{recruiter_email.lower().strip()}"
            rec_node = self.get_or_create_node(rec_id, "RECRUITER", recruiter_email)
            rec_node.verification_count += 1
            if is_risky:
                rec_node.scam_flags += 1
            self.add_edge(rec_id, comp_id, "RECRUITS_FOR")

        dom_node = None
        if domain:
            dom_id = f"domain:{domain.lower().strip()}"
            dom_node = self.get_or_create_node(dom_id, "DOMAIN", domain)
            dom_node.verification_count += 1
            if is_risky:
                dom_node.scam_flags += 1
            if rec_node:
                self.add_edge(rec_node.node_id, dom_node.node_id, "OPERATES_FROM")

        # Compute trust score (0.0 to 1.0)
        trust_score = 1.0
        if comp_node.verification_count > 0:
            scam_ratio = comp_node.scam_flags / comp_node.verification_count
            trust_score = max(0.0, 1.0 - (scam_ratio * 0.8))

        return {
            "company_node": comp_node.node_id,
            "recruiter_node": rec_node.node_id if rec_node else None,
            "domain_node": dom_node.node_id if dom_node else None,
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "computed_trust_score": round(trust_score, 2),
        }

    def get_neighbors(self, node_id: str) -> List[dict]:
        neighbors = []
        for edge in self._edges:
            if edge.source_id == node_id and edge.target_id in self._nodes:
                target = self._nodes[edge.target_id]
                neighbors.append({
                    "relation": edge.relation,
                    "target_id": target.node_id,
                    "target_name": target.name,
                    "target_type": target.node_type,
                })
        return neighbors
