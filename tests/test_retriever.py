from src.models import RiskCase
from src.retriever import Retriever


def test_retriever_returns_top3():
    rc = RiskCase.model_validate({
        "id": "RC-200",
        "title": "API key exposure in logs",
        "description": "API keys detected in application log files",
        "category": "data",
        "severity": "high",
        "owner": "o",
        "mitigation": "m",
        "impact": "high",
        "likelihood": "medium",
        "affected_assets": ["logs"],
        "reported_date": "2025-10-17",
        "detection_method": "scan",
    })
    res = Retriever().retrieve(rc, top_k=3)
    assert len(res) == 3
    for r in res:
        assert 0.0 <= r.score <= 1.0


def test_retriever_obvious_match_ranks_first():
    retriever = Retriever()
    target = next(c for c in retriever.past_decisions if c["id"] == "PD-003")
    rc = RiskCase.model_validate({
        "id": "RC-201",
        "title": target["title"],
        "description": target["description"],
        "category": target["category"],
        "severity": target["severity"],
        "owner": "o",
        "mitigation": "m",
        "impact": "med",
        "likelihood": "low",
        "affected_assets": ["x"],
        "reported_date": "2025-10-17",
        "detection_method": "manual",
    })
    res = retriever.retrieve(rc, top_k=1)
    assert len(res) == 1
    assert res[0].id == "PD-003"
