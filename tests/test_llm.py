
from src.checker import Checker
from src.llm import LLM, FakeLLMClient
from src.models import RiskCase
from src.retriever import Retriever


def make_case():
    return RiskCase.model_validate({
        "id": "RC-300",
        "title": "privilege escalation",
        "description": "user gained elevated privileges",
        "category": "access",
        "severity": "high",
        "owner": "bob",
        "mitigation": "review permissions",
        "impact": "high",
        "likelihood": "medium",
        "affected_assets": ["iam"],
        "reported_date": "2025-10-17",
        "detection_method": "audit",
    })


def test_llm_output_validates():
    rc = make_case()
    cr = Checker().check(rc)
    sc = Retriever().retrieve(rc, top_k=2)
    pkg_dict = {
        "package_id": "PKG-TEST",
        "risk_case_id": rc.id,
        "summary": "test summary",
        "completeness_report": cr.model_dump(),
        "missing_information": [],
        "similar_cases": [s.model_dump() for s in sc],
        "questions_for_experts": ["q1"],
        "status": "draft",
    }
    client = FakeLLMClient(pkg_dict)
    llm = LLM(client=client)
    pkg = llm.generate_package(rc, cr, sc)
    assert pkg.status == "draft"
    assert pkg.risk_case_id == rc.id


def test_llm_cited_ids_must_exist():
    rc = make_case()
    cr = Checker().check(rc)
    sc = Retriever().retrieve(rc, top_k=2)
    bad = {
        "package_id": "PKG-BAD",
        "risk_case_id": rc.id,
        "summary": "bad",
        "completeness_report": cr.model_dump(),
        "missing_information": [],
        "similar_cases": [{"id": "PD-999", "title": "x", "category": "y", "severity": "z", "outcome": "o", "reasoning": "r", "score": 0.9}],
        "questions_for_experts": [],
        "status": "draft",
    }
    client = FakeLLMClient(bad)
    llm = LLM(client=client)
    try:
        llm.generate_package(rc, cr, sc)
        assert False, "should have raised"
    except ValueError as e:
        assert "not in retrieved" in str(e)
