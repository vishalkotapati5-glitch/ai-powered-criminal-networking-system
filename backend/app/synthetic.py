import math
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import Entity, Transaction


def generate_synthetic_transactions(
    db: Session,
    count: int = 1200,
    anomaly_rate: float = 0.05,
    seed: int = 20261115,
    reference_prefix: str = "SYN",
) -> set[str]:
    """Append a reproducible synthetic transaction sample and return anomaly reference IDs for evaluation."""
    if count < 3 or count > 100_000:
        raise ValueError("count must be between 3 and 100000")
    if not 0 <= anomaly_rate <= 0.5:
        raise ValueError("anomaly_rate must be between 0 and 0.5")
    if not reference_prefix.isalnum() or len(reference_prefix) > 10:
        raise ValueError("reference_prefix must be 1-10 alphanumeric characters")

    entity_ids = [row.id for row in db.query(Entity.id).filter(Entity.entity_type == "person").all()]
    if len(entity_ids) < 2:
        raise ValueError("At least two fictional person entities are required")

    rng = random.Random(seed)
    anomaly_count = round(count * anomaly_rate)
    anomaly_indexes = set(rng.sample(range(count), anomaly_count))
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    anomaly_references: set[str] = set()
    transactions = []
    for index in range(count):
        source_index = rng.randrange(len(entity_ids))
        target_index = (source_index + rng.randrange(1, len(entity_ids))) % len(entity_ids)
        reference = f"{reference_prefix}-{index:08d}"
        is_anomaly = index in anomaly_indexes
        amount = rng.uniform(1300, 4000) if is_anomaly else math.exp(rng.gauss(4.5, 0.3))
        transactions.append(Transaction(
            reference=reference,
            source_entity_id=entity_ids[source_index],
            target_entity_id=entity_ids[target_index],
            amount=round(amount, 2),
            currency="USD",
            occurred_at=start + timedelta(seconds=index),
        ))
        if is_anomaly:
            anomaly_references.add(reference)
    db.add_all(transactions)
    db.flush()
    return anomaly_references
