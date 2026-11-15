import uuid
from collections import defaultdict
from datetime import datetime, timezone

import networkx as nx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AnalysisResult, AuditLog, Communication, Entity, Investigation, Location, Relationship, Transaction, User
from app.schemas import AnomalyRequest, Credentials, EntityOut, ReportRequest, TokenResponse
from app.security import create_access_token, hash_password, require_analyst, verify_password
from app.services.analytics import DISCLAIMER, build_graph, centrality_results, community_results, detect_anomalies, network_summary
from app.services.reporting import build_csv_bundle, build_pdf_report

router = APIRouter(prefix="/api")
limiter = Limiter(key_func=get_remote_address)


@router.post("/auth/register", response_model=TokenResponse)
@limiter.limit("5/minute")
def register(request: Request, credentials: Credentials, db: Session = Depends(get_db)):
    email = credentials.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=422, detail="A valid email is required")
    if db.query(User).filter(func.lower(User.email) == email).first():
        raise HTTPException(status_code=409, detail="Account already exists")
    user = User(email=email, password_hash=hash_password(credentials.password), role="analyst")
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user))


@router.post("/auth/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, credentials: Credentials, db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.email) == credentials.email.strip().lower()).first()
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user))


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/dashboard/overview")
def dashboard_overview(db: Session = Depends(get_db), _: User = Depends(require_analyst)):
    graph = build_graph(db)
    transactions = db.query(Transaction).count()
    anomaly_data = detect_anomalies(db)
    return {
        **network_summary(graph),
        "transaction_count": transactions,
        "anomaly_count": len(anomaly_data["findings"]),
        "recent_activity": [
            {"id": row.reference, "amount": row.amount, "source": row.source_entity_id, "target": row.target_entity_id, "occurred_at": row.occurred_at}
            for row in db.query(Transaction).order_by(Transaction.occurred_at.desc()).limit(6).all()
        ],
        "disclaimer": DISCLAIMER,
    }


@router.get("/dashboard/statistics")
def dashboard_statistics(db: Session = Depends(get_db), _: User = Depends(require_analyst)):
    rows = db.query(Entity.entity_type, func.count(Entity.id)).group_by(Entity.entity_type).all()
    return {"entities_by_type": [{"type": kind, "count": count} for kind, count in rows],
            "relationship_count": db.query(Relationship).count(),
            "transaction_count": db.query(Transaction).count()}


@router.get("/entities/search", response_model=list[EntityOut])
def search_entities(q: str = Query(min_length=1, max_length=100), db: Session = Depends(get_db), _: User = Depends(require_analyst)):
    term = f"%{q.strip()}%"
    return db.query(Entity).filter(or_(Entity.id.ilike(term), Entity.label.ilike(term))).order_by(Entity.id).limit(50).all()


@router.get("/entities", response_model=list[EntityOut])
def list_entities(entity_type: str | None = None, limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db), _: User = Depends(require_analyst)):
    query = db.query(Entity)
    if entity_type:
        query = query.filter(Entity.entity_type == entity_type)
    return query.order_by(Entity.id).limit(limit).all()


@router.get("/entities/{entity_id}", response_model=EntityOut)
def get_entity(entity_id: str, db: Session = Depends(get_db), _: User = Depends(require_analyst)):
    entity = db.get(Entity, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.get("/entities/{entity_id}/activity")
def entity_activity(entity_id: str, db: Session = Depends(get_db), _: User = Depends(require_analyst)):
    entity = db.get(Entity, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    relations = db.query(Relationship).filter(or_(Relationship.source_entity_id == entity_id, Relationship.target_entity_id == entity_id)).all()
    transactions = db.query(Transaction).filter(or_(Transaction.source_entity_id == entity_id, Transaction.target_entity_id == entity_id)).all()
    communications = db.query(Communication).filter(or_(Communication.source_entity_id == entity_id, Communication.target_entity_id == entity_id)).all()
    locations = db.query(Location).filter(Location.entity_id == entity_id).all()
    timeline = [
        {"kind": "relationship", "label": row.relationship_type, "related_entity": row.target_entity_id if row.source_entity_id == entity_id else row.source_entity_id, "occurred_at": row.occurred_at.isoformat()}
        for row in relations
    ] + [
        {"kind": "transaction", "label": row.reference, "amount": row.amount, "related_entity": row.target_entity_id if row.source_entity_id == entity_id else row.source_entity_id, "occurred_at": row.occurred_at.isoformat()}
        for row in transactions
    ] + [
        {"kind": "communication", "label": "Synthetic contact event", "related_entity": row.target_entity_id if row.source_entity_id == entity_id else row.source_entity_id, "occurred_at": row.occurred_at.isoformat()}
        for row in communications
    ] + [
        {"kind": "location", "label": row.location_code, "related_entity": None, "occurred_at": row.occurred_at.isoformat()}
        for row in locations
    ]
    return {"entity": EntityOut.model_validate(entity), "timeline": sorted(timeline, key=lambda item: item["occurred_at"], reverse=True)}


@router.get("/relationships")
def list_relationships(limit: int = Query(default=200, ge=1, le=1000), db: Session = Depends(get_db), _: User = Depends(require_analyst)):
    rows = db.query(Relationship).order_by(Relationship.id).limit(limit).all()
    return [{"id": row.id, "source": row.source_entity_id, "target": row.target_entity_id, "type": row.relationship_type, "weight": row.weight} for row in rows]


@router.get("/relationships/graph/{entity_id}")
def ego_graph(entity_id: str, depth: int = Query(default=2, ge=1, le=3), db: Session = Depends(get_db), _: User = Depends(require_analyst)):
    graph = build_graph(db)
    if entity_id not in graph:
        raise HTTPException(status_code=404, detail="Entity not found")
    included = {entity_id}
    frontier = {entity_id}
    for _ in range(depth):
        frontier = {neighbor for node in frontier for neighbor in graph.neighbors(node)} - included
        included |= frontier
    subgraph = graph.subgraph(included)
    return {"nodes": [{"id": node, **data} for node, data in subgraph.nodes(data=True)],
            "edges": [{"source": left, "target": right, **data} for left, right, data in subgraph.edges(data=True)]}


@router.post("/analysis/network")
def analyze_network(db: Session = Depends(get_db), _: User = Depends(require_analyst)):
    graph = build_graph(db)
    summary = network_summary(graph)
    return {**summary, "communities": community_results(graph), "disclaimer": "Graph metrics describe structure only, not intent or culpability."}


@router.get("/analysis/centrality")
def centrality(db: Session = Depends(get_db), _: User = Depends(require_analyst)):
    return {"results": centrality_results(build_graph(db))}


@router.get("/analysis/communities")
def communities(db: Session = Depends(get_db), _: User = Depends(require_analyst)):
    return {"communities": community_results(build_graph(db))}


@router.get("/analysis/patterns")
def discover_patterns(db: Session = Depends(get_db), _: User = Depends(require_analyst)):
    graph = build_graph(db)
    baseline_density = network_summary(graph)["density"]
    patterns = []
    for community in community_results(graph):
        if community["size"] < 3:
            continue
        density = nx.density(graph.subgraph(community["members"]))
        if density > baseline_density:
            patterns.append({
                "type": "dense_community",
                "label": f"Denser connected group ({community['size']} entities)",
                "entity_ids": community["members"],
                "explanation": f"This connected group has internal graph density {density:.2f}, above the overall network density {baseline_density:.2f}. Density is a structural description, not evidence of intent.",
            })

    shared_locations: dict[str, set[str]] = defaultdict(set)
    for location in db.query(Location).all():
        shared_locations[location.location_code].add(location.entity_id)
    for code, entity_ids in shared_locations.items():
        if len(entity_ids) >= 2:
            patterns.append({
                "type": "shared_location",
                "label": f"Repeated shared location record ({code})",
                "entity_ids": sorted(entity_ids),
                "explanation": "These fictional entities have records at the same synthetic location code. Shared records can have many ordinary explanations and require context.",
            })

    repeated_pairs: dict[tuple[str, str], list[str]] = defaultdict(list)
    for transaction in db.query(Transaction).all():
        repeated_pairs[tuple(sorted((transaction.source_entity_id, transaction.target_entity_id)))].append(transaction.reference)
    for pair, references in repeated_pairs.items():
        if len(references) >= 2:
            patterns.append({
                "type": "repeated_transaction_pair",
                "label": f"Repeated transaction pair ({len(references)} records)",
                "entity_ids": list(pair),
                "explanation": "The same fictional endpoint pair appears in multiple transaction records. Recurrence alone does not establish abnormality or wrongdoing.",
            })
    return {"patterns": patterns, "disclaimer": "Pattern discovery describes synthetic data only and must not be used as evidence or a person-level judgment."}


@router.get("/analysis/shortest-path")
def shortest_path(source_id: str, target_id: str, db: Session = Depends(get_db), _: User = Depends(require_analyst)):
    graph = build_graph(db)
    if source_id not in graph or target_id not in graph:
        raise HTTPException(status_code=404, detail="Source or target entity not found")
    try:
        path = nx.shortest_path(graph, source_id, target_id)
    except nx.NetworkXNoPath:
        return {"path": [], "length": None}
    return {"path": path, "length": len(path) - 1}


@router.post("/ml/anomaly-detection")
def run_anomaly_detection(payload: AnomalyRequest, db: Session = Depends(get_db), user: User = Depends(require_analyst)):
    result = detect_anomalies(db, payload.contamination)
    db.add(AnalysisResult(result_type="anomaly", payload=result))
    db.add(AuditLog(user_id=user.id, action="anomaly_analysis", resource="transactions"))
    db.commit()
    return result


@router.get("/ml/results")
def anomaly_results(db: Session = Depends(get_db), _: User = Depends(require_analyst)):
    latest = db.query(AnalysisResult).filter_by(result_type="anomaly").order_by(AnalysisResult.created_at.desc()).first()
    return latest.payload if latest else {"findings": [], "method": "Isolation Forest + DBSCAN", "limitations": DISCLAIMER}


@router.post("/reports/generate")
def generate_report(payload: ReportRequest, db: Session = Depends(get_db), user: User = Depends(require_analyst)):
    for entity_id in payload.entity_ids:
        if db.get(Entity, entity_id) is None:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
    report_id = f"INV-{uuid.uuid4().hex[:10].upper()}"
    investigation = Investigation(reference_id=report_id, title=payload.title, created_by=user.id, selected_entities=payload.entity_ids)
    db.add(investigation)
    db.flush()
    graph = build_graph(db)
    result = detect_anomalies(db)
    included = set(payload.entity_ids)
    if included:
        included.update(neighbor for entity_id in payload.entity_ids for neighbor in graph.neighbors(entity_id))
    else:
        included.update(graph.nodes)
    report_graph = graph.subgraph(included)
    summary = network_summary(report_graph)
    body = {"reference_id": report_id, "title": payload.title, "selected_entities": payload.entity_ids,
            "network_summary": summary, "anomaly_findings": result["findings"],
            "anomaly_method": result["method"],
            "anomaly_features": result["features"],
            "anomaly_sample_count": result["sample_count"],
            "anomaly_contamination": result.get("contamination", 0.05),
            "network_graph": {
                "nodes": [{"id": node, "label": data.get("label", node), "entity_type": data.get("entity_type", "unknown")} for node, data in report_graph.nodes(data=True)],
                "edges": [{"source": source, "target": target, **data} for source, target, data in report_graph.edges(data=True)],
            },
            "disclaimer": DISCLAIMER, "created_at": datetime.now(timezone.utc).isoformat()}
    db.add(AnalysisResult(investigation_id=investigation.id, result_type="report", payload=body))
    db.add(AuditLog(user_id=user.id, action="report_generated", resource=report_id))
    db.commit()
    return body


@router.get("/reports")
def list_reports(db: Session = Depends(get_db), _: User = Depends(require_analyst)):
    results = db.query(AnalysisResult).filter_by(result_type="report").order_by(AnalysisResult.created_at.desc()).limit(100).all()
    return [result.payload for result in results]


@router.get("/reports/{reference_id}/download")
def download_report(reference_id: str, format: str = Query(default="csv", pattern="^(csv|pdf)$"), db: Session = Depends(get_db), _: User = Depends(require_analyst)):
    result = db.query(AnalysisResult).filter_by(result_type="report").order_by(AnalysisResult.created_at.desc()).all()
    report = next((row.payload for row in result if row.payload.get("reference_id") == reference_id), None)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if format == "csv":
        return Response(build_csv_bundle(report), media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{reference_id}.csv.zip"'})

    return Response(build_pdf_report(report), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{reference_id}.pdf"'})
