from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.database import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="analyst")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class EntityType(Base):
    __tablename__ = "entity_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True, index=True)


class Entity(Base):
    __tablename__ = "entities"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    entity_type: Mapped[str] = mapped_column(ForeignKey("entity_types.name"), index=True)
    label: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Relationship(Base):
    __tablename__ = "relationships"
    __table_args__ = (
        Index("ix_relationship_source_target", "source_entity_id", "target_entity_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    source_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), index=True)
    target_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), index=True)
    relationship_type: Mapped[str] = mapped_column(String(40), index=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (CheckConstraint("amount >= 0", name="ck_transaction_amount_nonnegative"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True)
    source_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id"), index=True)
    target_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)


class Communication(Base):
    __tablename__ = "communications"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id"), index=True)
    target_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id"), index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)


class Location(Base):
    __tablename__ = "locations"
    id: Mapped[int] = mapped_column(primary_key=True)
    entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id"), index=True)
    location_code: Mapped[str] = mapped_column(String(40), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)


class Investigation(Base):
    __tablename__ = "investigations"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(160), default="Synthetic network review")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    selected_entities: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    investigation_id: Mapped[int | None] = mapped_column(ForeignKey("investigations.id"), nullable=True)
    result_type: Mapped[str] = mapped_column(String(40), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    resource: Mapped[str] = mapped_column(String(255), default="")
    status_code: Mapped[int] = mapped_column(Integer, default=200)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)
