"""
LifeLens Ω — Phase 5: Cross-Domain Trust Integrity Ledger
Implements §13 (Evidence Ledger), §25 (Provenance), §88/§100 (Unified Auditability)

Provides:
- Append-only, cryptographically hash-chained provenance ledger for all verification events
- Verification chain integrity verification (tamper-detection)
- Exportable audit trail for user empowerment and compliance transparency
"""
import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


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


class TrustIntegrityLedger:
    """
    Immutable, hash-chained ledger storing verified findings, provenance references,
    and audit metadata.
    """

    def __init__(self) -> None:
        self.chain: List[LedgerBlock] = []
        self._create_genesis_block()

    def _create_genesis_block(self) -> None:
        genesis = LedgerBlock(
            index=0,
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_id="GENESIS",
            entity_name="LIFELENS_ROOT_TRUST_ANCHOR",
            risk_level="INFO",
            confidence=1.0,
            evidence_hashes=["0" * 64],
            previous_hash="0" * 64,
            block_hash="GENESIS_HASH_LIFELENS_OMEGA_TRUST_SYSTEM",
        )
        self.chain.append(genesis)

    def _calculate_hash(
        self,
        index: int,
        timestamp: str,
        request_id: str,
        entity_name: str,
        risk_level: str,
        confidence: float,
        evidence_hashes: List[str],
        previous_hash: str,
    ) -> str:
        payload = f"{index}:{timestamp}:{request_id}:{entity_name}:{risk_level}:{confidence}:{','.join(evidence_hashes)}:{previous_hash}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def record_verification(
        self,
        request_id: str,
        entity_name: str,
        risk_level: str,
        confidence: float,
        evidence_list: Optional[List[Dict[str, Any]]] = None,
    ) -> LedgerBlock:
        """Appends a new verification event to the immutable integrity chain."""
        last_block = self.chain[-1]
        index = len(self.chain)
        timestamp = datetime.now(timezone.utc).isoformat()

        evidence_hashes = []
        if evidence_list:
            for ev in evidence_list:
                ev_str = json.dumps(ev, sort_keys=True)
                evidence_hashes.append(hashlib.sha256(ev_str.encode("utf-8")).hexdigest())
        else:
            evidence_hashes.append(hashlib.sha256(f"ev_{request_id}".encode("utf-8")).hexdigest())

        block_hash = self._calculate_hash(
            index=index,
            timestamp=timestamp,
            request_id=request_id,
            entity_name=entity_name,
            risk_level=risk_level,
            confidence=confidence,
            evidence_hashes=evidence_hashes,
            previous_hash=last_block.block_hash,
        )

        block = LedgerBlock(
            index=index,
            timestamp=timestamp,
            request_id=request_id,
            entity_name=entity_name,
            risk_level=risk_level,
            confidence=round(confidence, 3),
            evidence_hashes=evidence_hashes,
            previous_hash=last_block.block_hash,
            block_hash=block_hash,
        )
        self.chain.append(block)
        logger.info(f"Recorded verification block #{index} for {request_id} (hash={block_hash[:12]}...)")
        return block

    def verify_chain_integrity(self) -> bool:
        """Verifies that the entire hash chain is unbroken and free of tampering."""
        if len(self.chain) <= 1:
            return True

        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]

            if curr.previous_hash != prev.block_hash:
                logger.error(f"Chain broken at index {i}: previous_hash mismatch")
                return False

            recalculated = self._calculate_hash(
                index=curr.index,
                timestamp=curr.timestamp,
                request_id=curr.request_id,
                entity_name=curr.entity_name,
                risk_level=curr.risk_level,
                confidence=curr.confidence,
                evidence_hashes=curr.evidence_hashes,
                previous_hash=curr.previous_hash,
            )
            if curr.block_hash != recalculated:
                logger.error(f"Chain corrupted at index {i}: block_hash mismatch")
                return False

        return True

    def export_audit_trail(self, request_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Exports ledger blocks, optionally filtered by request_id."""
        if request_id:
            return [asdict(b) for b in self.chain if b.request_id == request_id]
        return [asdict(b) for b in self.chain]
