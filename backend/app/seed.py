from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Communication, Entity, EntityType, Location, Relationship, Transaction, User
from app.security import hash_password

ENTITY_TYPES = ("person", "phone", "location", "organization", "transaction")


def seed_database(db: Session) -> None:
    if db.query(Entity).first():
        return
    for name in ENTITY_TYPES:
        db.add(EntityType(name=name))
    db.flush()

    entities: list[Entity] = []
    for i in range(1, 13):
        entities.append(Entity(id=f"PER-{i:03}", entity_type="person", label=f"Fictional Person {i:03}", description="Synthetic profile; no real person represented.", extra_data={"dataset": "fictional-v1"}))
    for i in range(1, 7):
        entities.append(Entity(id=f"ORG-{i:03}", entity_type="organization", label=f"Fictional Group {i:03}", description="Synthetic organization.", extra_data={"dataset": "fictional-v1"}))
    for i in range(1, 7):
        entities.append(Entity(id=f"PHN-{i:03}", entity_type="phone", label=f"555-010{i}", description="Reserved fictional contact identifier.", extra_data={"dataset": "fictional-v1"}))
    for i in range(1, 7):
        entities.append(Entity(id=f"LOC-{i:03}", entity_type="location", label=f"Fictional Zone {i:03}", description="Synthetic location code.", extra_data={"dataset": "fictional-v1"}))
    db.add_all(entities)
    db.flush()

    base = datetime.now(timezone.utc)
    relationships: list[Relationship] = []
    for i in range(1, 13):
        group = (i - 1) // 4 + 1
        relationships.append(Relationship(source_entity_id=f"PER-{i:03}", target_entity_id=f"ORG-{group:03}", relationship_type="organizational_connection", weight=1.0, occurred_at=base - timedelta(days=i)))
        relationships.append(Relationship(source_entity_id=f"PER-{i:03}", target_entity_id=f"PHN-{(i - 1) % 6 + 1:03}", relationship_type="communication", weight=1.0, occurred_at=base - timedelta(days=i * 2)))
        relationships.append(Relationship(source_entity_id=f"PER-{i:03}", target_entity_id=f"LOC-{(i - 1) % 6 + 1:03}", relationship_type="shared_location", weight=1.0, occurred_at=base - timedelta(days=i * 3)))
        if i % 4:
            relationships.append(Relationship(source_entity_id=f"PER-{i:03}", target_entity_id=f"PER-{i + 1:03}", relationship_type="associated_entity", weight=1.0, occurred_at=base - timedelta(days=i)))
    db.add_all(relationships)

    for i in range(1, 25):
        source = (i - 1) % 12 + 1
        target = (i * 5) % 12 + 1
        if source == target:
            target = target % 12 + 1
        amount = float([45, 80, 120, 200, 320, 95, 140, 180][i % 8])
        if i in (7, 19):
            amount = 2400.0
        db.add(Transaction(reference=f"TX-{i:04}", source_entity_id=f"PER-{source:03}", target_entity_id=f"PER-{target:03}", amount=amount, occurred_at=base - timedelta(days=i)))
    for i in range(1, 13):
        db.add(Communication(source_entity_id=f"PER-{i:03}", target_entity_id=f"PHN-{(i - 1) % 6 + 1:03}", duration_seconds=30 + i * 7, occurred_at=base - timedelta(hours=i)))
        db.add(Location(entity_id=f"PER-{i:03}", location_code=f"ZONE-{(i - 1) % 6 + 1:03}", occurred_at=base - timedelta(days=i)))

    if not db.query(User).filter_by(email=settings.demo_email).first():
        db.add(User(email=settings.demo_email, password_hash=hash_password(settings.demo_password), role="analyst"))
    db.commit()
