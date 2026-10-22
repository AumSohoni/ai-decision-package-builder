import pytest
from fastapi.testclient import TestClient

from web.app import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app(audit_log_path=tmp_path / "audit.jsonl", use_mock_llm=True)
    with TestClient(app) as c:
        yield c


def sample_case():
    return {
        "id": "RC-001",
        "title": "API key exposure in logs",
        "description": "API keys detected in application log files during a routine scan.",
        "category": "data",
        "severity": "high",
        "owner": "alice",
        "mitigation": "Rotate keys and redact logs.",
        "impact": "high",
        "likelihood": "medium",
        "affected_assets": ["logging_service", "api_gateway"],
        "reported_date": "2025-10-15",
        "detection_method": "automated_scan",
    }


def test_index_serves_ui(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Decision Desk" in res.text


def test_analyze_returns_report_and_draft(client):
    res = client.post("/api/analyze", json=sample_case())
    assert res.status_code == 200
    body = res.json()
    assert body["completeness_report"]["is_complete"] is True
    assert len(body["similar_cases"]) == 3
    assert body["package"]["status"] == "draft"
    assert body["package"]["risk_case_id"] == "RC-001"


def test_analyze_flags_incomplete_case(client):
    payload = sample_case()
    for field in ("impact", "likelihood", "affected_assets"):
        payload.pop(field)
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    report = res.json()["completeness_report"]
    assert report["is_complete"] is False
    missing = {m["field"] for m in report["missing"]}
    assert {"impact", "likelihood", "affected_assets"} <= missing


def test_analyze_rejects_missing_core_field(client):
    payload = sample_case()
    payload.pop("title")
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 422


def test_review_requires_reviewer_name(client):
    pkg = client.post("/api/analyze", json=sample_case()).json()["package"]
    res = client.post(
        "/api/review",
        json={"package_id": pkg["package_id"], "reviewer_name": "  ", "action": "approve"},
    )
    assert res.status_code == 400
    assert client.get("/api/audit").json()["entries"] == []


def test_review_approve_persists_and_audits(client):
    pkg = client.post("/api/analyze", json=sample_case()).json()["package"]
    res = client.post(
        "/api/review",
        json={
            "package_id": pkg["package_id"],
            "reviewer_name": "Jane Doe",
            "action": "approve",
            "reason": "matches PD-008",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["package"]["status"] == "approved"
    assert body["package"]["reviewer_name"] == "Jane Doe"

    entries = client.get("/api/audit").json()["entries"]
    assert len(entries) == 1
    assert entries[0]["action"] == "approve"
    assert entries[0]["reviewer_name"] == "Jane Doe"


def test_review_rejects_unknown_package(client):
    res = client.post(
        "/api/review",
        json={"package_id": "PKG-NOPE", "reviewer_name": "Jane", "action": "approve"},
    )
    assert res.status_code == 404


def test_review_rejects_invalid_action(client):
    pkg = client.post("/api/analyze", json=sample_case()).json()["package"]
    res = client.post(
        "/api/review",
        json={"package_id": pkg["package_id"], "reviewer_name": "Jane", "action": "maybe"},
    )
    assert res.status_code == 400


def test_provider_status_endpoint(client):
    res = client.get("/api/provider")
    assert res.status_code == 200
    body = res.json()
    assert "provider" in body
    assert "real_available" in body
    assert body["default_mock"] is True


def test_analyze_reports_mock_mode(client):
    res = client.post("/api/analyze?use_mock=true", json=sample_case())
    assert res.status_code == 200
    assert res.json()["used_mock"] is True

