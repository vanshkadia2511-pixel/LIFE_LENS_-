"""
LifeLens Ω - Data Access Repositories
Clean repository pattern over the SQLAlchemy models.
"""

from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import logging

from .models import (
    UserModel, EntityModel, BaselineModel,
    EventModel, AssessmentModel, AuditLogModel,
    RiskLevelEnum, FrictionLevelEnum
)

logger = logging.getLogger(__name__)


class UserRepository:
    """Data access layer for users."""

    @staticmethod
    def create_user(db: Session, user_id: str, email: str) -> UserModel:
        user = UserModel(user_id=user_id, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"User created: {user_id}")
        return user

    @staticmethod
    def get_user(db: Session, user_id: str) -> Optional[UserModel]:
        return db.query(UserModel).filter(UserModel.user_id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[UserModel]:
        return db.query(UserModel).filter(UserModel.email == email).first()


class EntityRepository:
    """Data access layer for entities."""

    @staticmethod
    def create_entity(db: Session, entity_id: str, user_id: str, **kwargs) -> EntityModel:
        entity = EntityModel(entity_id=entity_id, user_id=user_id, **kwargs)
        db.add(entity)
        db.commit()
        db.refresh(entity)
        logger.info(f"Entity created: {entity_id} for user {user_id}")
        return entity

    @staticmethod
    def get_entity(db: Session, entity_id: str) -> Optional[EntityModel]:
        return db.query(EntityModel).filter(EntityModel.entity_id == entity_id).first()

    @staticmethod
    def get_entities_by_user(db: Session, user_id: str) -> List[EntityModel]:
        return db.query(EntityModel).filter(EntityModel.user_id == user_id).all()

    @staticmethod
    def find_similar_entity(db: Session, user_id: str, claimed_identity: str) -> Optional[EntityModel]:
        return db.query(EntityModel).filter(
            EntityModel.user_id == user_id,
            EntityModel.claimed_identity.ilike(f"%{claimed_identity}%")
        ).first()


class EventRepository:
    """Data access layer for events."""

    @staticmethod
    def create_event(db: Session, event_id: str, user_id: str, **kwargs) -> EventModel:
        event = EventModel(event_id=event_id, user_id=user_id, **kwargs)
        db.add(event)
        db.commit()
        db.refresh(event)
        logger.info(f"Event created: {event_id}")
        return event

    @staticmethod
    def get_event(db: Session, event_id: str) -> Optional[EventModel]:
        return db.query(EventModel).filter(EventModel.event_id == event_id).first()

    @staticmethod
    def get_events_by_user(db: Session, user_id: str, limit: int = 100) -> List[EventModel]:
        return db.query(EventModel).filter(
            EventModel.user_id == user_id,
            EventModel.deleted_at == None  # noqa: E711
        ).order_by(EventModel.timestamp.desc()).limit(limit).all()

    @staticmethod
    def get_events_by_entity(db: Session, entity_id: str, limit: int = 50) -> List[EventModel]:
        return db.query(EventModel).filter(
            EventModel.source_entity_id == entity_id,
            EventModel.deleted_at == None  # noqa: E711
        ).order_by(EventModel.timestamp.desc()).limit(limit).all()


class AssessmentRepository:
    """Data access layer for assessments."""

    @staticmethod
    def create_assessment(
        db: Session,
        assessment_id: str,
        event_id: str,
        user_id: str,
        **kwargs
    ) -> AssessmentModel:
        assessment = AssessmentModel(
            assessment_id=assessment_id,
            event_id=event_id,
            user_id=user_id,
            **kwargs
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        logger.info(f"Assessment created: {assessment_id} for event {event_id}")
        return assessment

    @staticmethod
    def get_assessment(db: Session, assessment_id: str) -> Optional[AssessmentModel]:
        return db.query(AssessmentModel).filter(
            AssessmentModel.assessment_id == assessment_id
        ).first()

    @staticmethod
    def get_assessment_by_event(db: Session, event_id: str) -> Optional[AssessmentModel]:
        return db.query(AssessmentModel).filter(
            AssessmentModel.event_id == event_id
        ).first()


class AuditRepository:
    """Data access layer for audit logs."""

    @staticmethod
    def log_action(
        db: Session,
        log_id: str,
        action: str,
        user_id: Optional[str] = None,
        event_id: Optional[str] = None,
        **kwargs
    ) -> AuditLogModel:
        log = AuditLogModel(
            log_id=log_id,
            action=action,
            user_id=user_id,
            event_id=event_id,
            **kwargs
        )
        db.add(log)
        db.commit()
        return log
