from __future__ import annotations

from src.checker import Checker
from src.models import RiskCase


def test_checker_complete():
    case = {
        "id": "RC-100",
        "title": "t",
        "description": "d",
        "category": "data",
        "severity": "high",
        "owner": "o",
        "mitigation": "m",
        "impact": "high",
        "likelihood": "medium",
        "affected_assets": ["a"],
        "reported_date": "2025-10-17",
        "detection_method": "scan",
    }
    rc = RiskCase.model_validate(case)
    cr = Checker().check(rc)
    assert cr.is_complete
    assert cr.completeness_score == 100


def test_checker_missing_one():
    case = {
        "id": "RC-101",
        "title": "t",
        "description": "d",
        "category": "data",
        "severity": "high",
        "owner": "o",
        "mitigation": "m",
        # missing impact
        "likelihood": "medium",
        "affected_assets": ["a"],
        "reported_date": "2025-10-17",
        "detection_method": "scan",
    }
    rc = RiskCase.model_validate(case)
    cr = Checker().check(rc)
    assert not cr.is_complete
    assert any(m.field == "impact" for m in cr.missing)


def test_checker_missing_several():
    case = {
        "id": "RC-102",
        "title": "t",
        "description": "d",
        "category": "data",
        "severity": "high",
        "owner": "o",
        "mitigation": "m",
    }
    rc = RiskCase.model_validate(case)
    cr = Checker().check(rc)
    assert not cr.is_complete
    assert len(cr.missing) >= 4
