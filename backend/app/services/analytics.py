from collections import Counter

import networkx as nx
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
from sqlalchemy.orm import Session

from app.models import Entity, Relationship, Transaction

DISCLAIMER = "Exploratory lead only. This statistical pattern is not proof of wrongdoing and must not be used to label a person."


def build_graph(db: Session) -> nx.Graph:
    graph = nx.Graph()
    for entity in db.query(Entity).all():
        graph.add_node(entity.id, label=entity.label, entity_type=entity.entity_type)
    for relation in db.query(Relationship).all():
        graph.add_edge(relation.source_entity_id, relation.target_entity_id, type=relation.relationship_type, weight=relation.weight)
    return graph


def network_summary(graph: nx.Graph) -> dict:
    components = sorted((sorted(component) for component in nx.connected_components(graph)), key=len, reverse=True)
    return {
        "entity_count": graph.number_of_nodes(),
        "relationship_count": graph.number_of_edges(),
        "component_count": len(components),
        "density": round(nx.density(graph), 4) if graph.number_of_nodes() > 1 else 0,
        "largest_component": components[0] if components else [],
    }


def centrality_results(graph: nx.Graph) -> list[dict]:
    degree = nx.degree_centrality(graph)
    between = nx.betweenness_centrality(graph, normalized=True)
    close = nx.closeness_centrality(graph)
    pagerank = nx.pagerank(graph) if graph.number_of_nodes() else {}
    return [
        {"entity_id": node, "label": data.get("label", node), "entity_type": data.get("entity_type", "unknown"),
         "degree": round(degree.get(node, 0), 4), "betweenness": round(between.get(node, 0), 4),
         "closeness": round(close.get(node, 0), 4), "pagerank": round(pagerank.get(node, 0), 4)}
        for node, data in graph.nodes(data=True)
    ]


def community_results(graph: nx.Graph) -> list[dict]:
    if graph.number_of_edges() == 0:
        return []
    communities = nx.community.greedy_modularity_communities(graph)
    return [{"community_id": i + 1, "members": sorted(group), "size": len(group)} for i, group in enumerate(sorted(communities, key=len, reverse=True))]


def detect_anomalies(db: Session, contamination: float = 0.05) -> dict:
    rows = db.query(Transaction).order_by(Transaction.occurred_at).all()
    if len(rows) < 3:
        return {
            "findings": [],
            "method": "Isolation Forest + DBSCAN",
            "sample_count": len(rows),
            "features": ["log_transaction_amount", "combined_endpoint_transaction_count"],
            "limitations": "At least three transaction records are required. " + DISCLAIMER,
        }

    counts = Counter()
    for row in rows:
        counts[row.source_entity_id] += 1
        counts[row.target_entity_id] += 1
    amounts = np.asarray([row.amount for row in rows], dtype=float)
    endpoint_activity = np.asarray([
        counts[row.source_entity_id] + counts[row.target_entity_id] for row in rows
    ], dtype=float)
    features = np.column_stack((np.log1p(amounts), endpoint_activity))
    if np.unique(features, axis=0).shape[0] < 2:
        return {
            "findings": [],
            "method": "Isolation Forest + DBSCAN",
            "sample_count": len(rows),
            "features": ["log_transaction_amount", "combined_endpoint_transaction_count"],
            "limitations": "The dataset has no feature variation from which to distinguish outliers. " + DISCLAIMER,
        }

    model = IsolationForest(contamination=contamination, random_state=42, n_estimators=100)
    model.fit(features)
    predictions = model.predict(features)
    scores = -model.score_samples(features)
    normalized = (scores - scores.min()) / (scores.max() - scores.min() + 1e-9)
    scaled_amounts = RobustScaler().fit_transform(amounts.reshape(-1, 1))
    cluster_labels = DBSCAN(
        eps=0.75,
        min_samples=min(5, len(rows)),
    ).fit_predict(scaled_amounts)

    findings = []
    for index, row in enumerate(rows):
        is_isolated = predictions[index] == -1
        is_sparse_cluster = cluster_labels[index] == -1
        if not (is_isolated or is_sparse_cluster):
            continue
        reasons = []
        if is_isolated:
            reasons.append("transaction amount and combined endpoint activity differ from the synthetic dataset baseline")
        if is_sparse_cluster:
            reasons.append("amount falls outside dense amount clusters in this synthetic sample")
        findings.append({
            "transaction_id": row.reference,
            "entity_ids": [row.source_entity_id, row.target_entity_id],
            "amount": row.amount,
            "currency": row.currency,
            "score": round(float(normalized[index]), 3),
            "confidence": "exploratory",
            "signals": {"isolation_forest": bool(is_isolated), "dbscan": bool(is_sparse_cluster)},
            "explanation": "; ".join(reasons),
            "limitations": DISCLAIMER,
        })
    findings.sort(key=lambda item: item["score"], reverse=True)
    return {
        "findings": findings,
        "method": "Isolation Forest + DBSCAN",
        "sample_count": len(rows),
        "features": ["log_transaction_amount", "combined_endpoint_transaction_count"],
        "contamination": contamination,
        "limitations": "Outlier scores are relative to the analyzed sample, not calibrated probabilities. " + DISCLAIMER,
    }
