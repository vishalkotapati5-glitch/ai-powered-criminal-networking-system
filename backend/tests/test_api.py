import csv
import io
import zipfile

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.database as database
import app.main as main
from app.database import Base
from app.models import AuditLog


@pytest.fixture
def client(monkeypatch):
    test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    test_sessions = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "SessionLocal", test_sessions)
    monkeypatch.setattr(main, "SessionLocal", test_sessions)
    Base.metadata.create_all(bind=test_engine)
    with TestClient(main.app) as test_client:
        yield test_client
    test_engine.dispose()


def test_login_protects_and_serves_synthetic_analysis(client):
    denied = client.get("/api/entities")
    assert denied.status_code == 401

    login = client.post("/api/auth/login", json={"email": "analyst@fictional.test", "password": "demo-pass-01"})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    overview = client.get("/api/dashboard/overview", headers=headers)
    assert overview.status_code == 200
    assert overview.json()["entity_count"] == 30

    profile = client.get("/api/entities/PER-001/activity", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["entity"]["id"] == "PER-001"
    assert any(event["kind"] == "transaction" for event in profile.json()["timeline"])

    patterns = client.get("/api/analysis/patterns", headers=headers)
    assert patterns.status_code == 200
    assert patterns.json()["patterns"]

    report = client.post("/api/reports/generate", headers=headers, json={"title": "Synthetic review", "entity_ids": ["PER-001"]})
    assert report.status_code == 200
    assert report.json()["network_graph"]["nodes"]
    reference = report.json()["reference_id"]
    csv_report = client.get(f"/api/reports/{reference}/download?format=csv", headers=headers)
    pdf_report = client.get(f"/api/reports/{reference}/download?format=pdf", headers=headers)
    assert csv_report.status_code == 200 and "application/zip" in csv_report.headers["content-type"]
    with zipfile.ZipFile(io.BytesIO(csv_report.content)) as bundle:
        assert {"summary.csv", "anomaly_findings.csv", "entities.csv", "relationships.csv"} <= set(bundle.namelist())
        summary_rows = list(csv.DictReader(io.StringIO(bundle.read("summary.csv").decode("utf-8-sig"))))
        findings_rows = list(csv.DictReader(io.StringIO(bundle.read("anomaly_findings.csv").decode("utf-8-sig"))))
        assert any(row["field"] == "anomaly_method" for row in summary_rows)
        assert len(findings_rows) == len(report.json()["anomaly_findings"])
        if findings_rows:
            assert {"source_entity_id", "outlier_score", "explanation"} <= set(findings_rows[0])
    assert pdf_report.status_code == 200 and pdf_report.content.startswith(b"%PDF")
    pdf_text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(pdf_report.content)).pages)
    assert "Detailed anomaly findings" in pdf_text
    assert "Network visualization" in pdf_text
    if report.json()["anomaly_findings"]:
        assert report.json()["anomaly_findings"][0]["transaction_id"] in pdf_text

    with main.SessionLocal() as db:
        audit_entry = db.query(AuditLog).filter_by(action="api_request", resource="/api/dashboard/overview").one()
        assert audit_entry.user_id is not None
