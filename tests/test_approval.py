from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.approval import ApprovalGate
from src.models import CompletenessReport, DecisionPackage


def make_pkg():
    cr = CompletenessReport(is_complete=False, missing=[], completeness_score=50, notes=[])
    return DecisionPackage(
        package_id="PKG-APP",
        risk_case_id="RC-400",
        summary="s",
        completeness_report=cr,
        missing_information=[],
        similar_cases=[],
        questions_for_experts=[],
        status="draft",
    )


def test_approval_requires_reviewer_name():
    pkg = make_pkg()
    with tempfile.TemporaryDirectory() as d:
        gate = ApprovalGate(audit_log_path=Path(d) / "audit.jsonl")
        try:
            gate.approve(pkg, "", reason="x")
            assert False
        except ValueError:
            pass
        try:
            gate.reject(pkg, "   ", reason="y")
            assert False
        except ValueError:
            pass


def test_approval_writes_audit_log_and_sets_status():
    pkg = make_pkg()
    with tempfile.TemporaryDirectory() as d:
        log = Path(d) / "audit.jsonl"
        gate = ApprovalGate(audit_log_path=log)
        rec = gate.approve(pkg, "alice", reason="ok")
        assert pkg.status == "approved"
        assert pkg.reviewer_name == "alice"
        assert rec.action == "approve"
        assert log.exists()
        with log.open("r") as f:
            lines = f.readlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["reviewer_name"] == "alice"
        assert data["package_id"] == "PKG-APP"


def test_approval_reject_sets_status():
    pkg = make_pkg()
    with tempfile.TemporaryDirectory() as d:
        gate = ApprovalGate(audit_log_path=Path(d) / "audit.jsonl")
        rec = gate.reject(pkg, "bob", reason="insufficient")
        assert pkg.status == "rejected"
        assert rec.action == "reject"
