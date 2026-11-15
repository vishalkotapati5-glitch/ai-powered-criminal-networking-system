from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Entity, EntityType, Relationship, Transaction
from app.services.analytics import build_graph, detect_anomalies, network_summary
from app.synthetic import generate_synthetic_transactions


def make_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def test_network_summary_counts_entities_and_components():
    db = make_db()
    db.add_all([EntityType(name="person"), EntityType(name="organization")])
    db.add_all([Entity(id="P-1", entity_type="person", label="Fictional 1"),
                Entity(id="P-2", entity_type="person", label="Fictional 2"),
                Entity(id="O-1", entity_type="organization", label="Fictional group")])
    db.add(Relationship(source_entity_id="P-1", target_entity_id="P-2", relationship_type="associated_entity"))
    db.commit()
    result = network_summary(build_graph(db))
    assert result["entity_count"] == 3
    assert result["relationship_count"] == 1
    assert result["component_count"] == 2
    db.close()


def test_anomaly_pipeline_handles_small_dataset_without_failure():
    db = make_db()
    db.add(EntityType(name="person"))
    db.add_all([Entity(id=f"P-{i}", entity_type="person", label=f"Fictional {i}") for i in range(3)])
    db.add_all([Transaction(reference=f"T-{i}", source_entity_id="P-0", target_entity_id=f"P-{i}", amount=float(i + 10)) for i in range(2)])
    db.commit()
    result = detect_anomalies(db)
    assert result["findings"] == []
    assert "not proof" in result["limitations"]
    db.close()


def test_large_synthetic_dataset_has_reproducible_anomaly_recall():
    db = make_db()
    db.add(EntityType(name="person"))
    db.add_all([
        Entity(id=f"P-{index:03}", entity_type="person", label=f"Fictional entity {index:03}")
        for index in range(100)
    ])
    db.commit()
    known_anomalies = generate_synthetic_transactions(db, count=1200, anomaly_rate=0.05)
    db.commit()

    result = detect_anomalies(db, contamination=0.05)
    predicted = {item["transaction_id"] for item in result["findings"]}
    true_positives = len(predicted & known_anomalies)
    precision = true_positives / len(predicted)
    recall = true_positives / len(known_anomalies)

    assert result["sample_count"] == 1200
    assert len(known_anomalies) == 60
    assert precision >= 0.80
    assert recall >= 0.95
    assert all("sensitive" not in name for name in result["features"])
    db.close()


def test_anomaly_pipeline_returns_no_signal_for_constant_features():
    db = make_db()
    db.add(EntityType(name="person"))
    db.add_all([Entity(id=f"P-{index}", entity_type="person", label=f"Fictional {index}") for index in range(2)])
    db.add_all([
        Transaction(reference=f"CONSTANT-{index}", source_entity_id="P-0", target_entity_id="P-1",
                    amount=100.0)
        for index in range(10)
    ])
    db.commit()

    result = detect_anomalies(db)
    assert result["findings"] == []
    assert "no feature variation" in result["limitations"]
    db.close()
