"""
LifeLens Ω — Database Repositories
Implementation Plan §39–40

CRUD operations for all 10 tables.
"""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional
import uuid

from sqlalchemy.orm import Session

from .db_models import (
    VerificationRequestDB, EntityDB, ClaimDB, EvidenceDB,
    RiskSignalDB, CECTAssessmentDB, VerificationSourceDB,
    UserFeedbackDB, AuditEventDB, AdapterRunDB,
)


class VerificationRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> VerificationRequestDB:
        obj = VerificationRequestDB(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get(self, request_id: str) -> Optional[VerificationRequestDB]:
        return self.db.query(VerificationRequestDB).filter(
            VerificationRequestDB.id == request_id
        ).first()

    def update_status(self, request_id: str, status: str) -> None:
        self.db.query(VerificationRequestDB).filter(
            VerificationRequestDB.id == request_id
        ).update({"status": status})
        self.db.commit()

    def update_result(
        self, request_id: str, risk_level: str, risk_confidence: str,
        cect_version: str, risk_config_version: str, extractor_version: str,
    ) -> None:
        self.db.query(VerificationRequestDB).filter(
            VerificationRequestDB.id == request_id
        ).update({
            "status": "COMPLETE",
            "risk_level": risk_level,
            "risk_confidence": risk_confidence,
            "cect_version": cect_version,
            "risk_config_version": risk_config_version,
            "extractor_version": extractor_version,
        })
        self.db.commit()


class EntityRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> EntityDB:
        obj = EntityDB(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list_for_request(self, request_id: str) -> List[EntityDB]:
        return self.db.query(EntityDB).filter(
            EntityDB.request_id == request_id
        ).all()


class ClaimRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> ClaimDB:
        obj = ClaimDB(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list_for_entity(self, entity_id: str) -> List[ClaimDB]:
        return self.db.query(ClaimDB).filter(
            ClaimDB.entity_id == entity_id
        ).all()


class EvidenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> EvidenceDB:
        obj = EvidenceDB(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list_for_claim(self, claim_id: str) -> List[EvidenceDB]:
        return self.db.query(EvidenceDB).filter(
            EvidenceDB.claim_id == claim_id
        ).all()


class RiskSignalRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> RiskSignalDB:
        obj = RiskSignalDB(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list_for_request(self, request_id: str) -> List[RiskSignalDB]:
        return self.db.query(RiskSignalDB).filter(
            RiskSignalDB.request_id == request_id
        ).all()


class CECTAssessmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> CECTAssessmentDB:
        obj = CECTAssessmentDB(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_for_request(self, request_id: str) -> Optional[CECTAssessmentDB]:
        return self.db.query(CECTAssessmentDB).filter(
            CECTAssessmentDB.request_id == request_id
        ).first()


class VerificationSourceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> VerificationSourceDB:
        obj = VerificationSourceDB(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list_for_request(self, request_id: str) -> List[VerificationSourceDB]:
        return self.db.query(VerificationSourceDB).filter(
            VerificationSourceDB.request_id == request_id
        ).all()


class UserFeedbackRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> UserFeedbackDB:
        obj = UserFeedbackDB(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        event_type: str,
        action: str,
        request_id: Optional[str] = None,
        actor: Optional[str] = None,
        resource: Optional[str] = None,
        result: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Record an audit event (§72).
        Do NOT log passwords, tokens, or unnecessary private data.
        """
        obj = AuditEventDB(
            request_id=request_id,
            event_type=event_type,
            actor=actor or "system",
            resource=resource,
            action=action,
            result=result,
            event_metadata=metadata or {},
        )
        self.db.add(obj)
        self.db.commit()


class AdapterRunRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> AdapterRunDB:
        obj = AdapterRunDB(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
