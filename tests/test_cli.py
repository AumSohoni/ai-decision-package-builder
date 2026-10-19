import json
from pathlib import Path

from src.cli import main

SAMPLE = Path(__file__).parent.parent / "examples" / "sample.json"


def _run(tmp_path, *extra):
    out_dir = tmp_path / "out"
    audit = tmp_path / "audit.jsonl"
    argv = [
        "--input",
        str(SAMPLE),
        "--use-mock-llm",
        "--out",
        str(out_dir),
        "--audit-log",
        str(audit),
        *extra,
    ]
    code = main(argv)
    pkg_path = out_dir / "decision_package_RC-001.json"
    return code, pkg_path, audit


def test_non_interactive_approve_persists_status(tmp_path):
    code, pkg_path, audit = _run(
        tmp_path, "--reviewer", "Jane", "--action", "approve", "--reason", "ok"
    )
    assert code == 0
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    assert pkg["status"] == "approved"
    assert pkg["reviewer_name"] == "Jane"
    assert pkg["approval_reason"] == "ok"
    assert pkg["reviewed_at"] is not None

    records = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1
    assert records[0]["action"] == "approve"
    assert records[0]["reviewer_name"] == "Jane"


def test_non_interactive_reject_persists_status(tmp_path):
    code, pkg_path, audit = _run(
        tmp_path, "--reviewer", "Sam", "--action", "reject", "--reason", "incomplete"
    )
    assert code == 0
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    assert pkg["status"] == "rejected"
    assert pkg["reviewer_name"] == "Sam"

    records = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    assert records[0]["action"] == "reject"


def test_no_review_leaves_draft(tmp_path, monkeypatch):
    def raise_eof(*_args, **_kwargs):
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)
    code, pkg_path, audit = _run(tmp_path)
    assert code == 0
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    assert pkg["status"] == "draft"
    assert not audit.exists()
