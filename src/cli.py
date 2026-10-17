from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

from .checker import Checker
from .llm import LLM, FakeLLMClient
from .models import DecisionPackage, RiskCase
from .retriever import Retriever
from .approval import ApprovalGate


def load_risk_case(path: str | Path) -> RiskCase:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    return RiskCase.model_validate(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI Decision Package Builder")
    parser.add_argument("--input", required=True, help="Path to risk case JSON file")
    parser.add_argument(
        "--use-mock-llm",
        action="store_true",
        help="Use fake LLM client for deterministic runs",
    )
    parser.add_argument("--out", default="out", help="Output directory for decision package")
    parser.add_argument("--audit-log", default=None, help="Path to audit log JSONL")
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        risk_case = load_risk_case(args.input)
    except Exception as e:
        print(f"Failed to load risk case: {e}", file=sys.stderr)
        return 1

    checker = Checker()
    completeness_report = checker.check(risk_case)

    retriever = Retriever()
    similar_cases = retriever.retrieve(risk_case, top_k=3)

    if args.use_mock_llm:
        # Build a sensible mock package
        pkg_dict = {
            "package_id": f"PKG-{uuid.uuid4().hex[:8].upper()}",
            "risk_case_id": risk_case.id,
            "summary": f"Summary for {risk_case.title}.",
            "completeness_report": completeness_report.model_dump(),
            "missing_information": [m.field for m in completeness_report.missing],
            "similar_cases": [s.model_dump() for s in similar_cases],
            "questions_for_experts": [
                "Is the proposed mitigation sufficient given severity?",
                "Are there additional affected assets to consider?",
            ],
            "status": "draft",
        }
        # Enforce only retrieved ids
        retrieved_ids = {s.id for s in similar_cases}
        pkg_dict["similar_cases"] = [
            s for s in pkg_dict["similar_cases"] if s["id"] in retrieved_ids
        ]
        client = FakeLLMClient(pkg_dict)
        llm = LLM(client=client)
    else:
        llm = LLM()

    try:
        package = llm.generate_package(risk_case, completeness_report, similar_cases)
    except Exception as e:
        print(f"Failed to generate decision package: {e}", file=sys.stderr)
        return 1

    pkg_path = out_dir / f"decision_package_{risk_case.id}.json"
    with pkg_path.open("w", encoding="utf-8") as f:
        f.write(package.model_dump_json(indent=2))

    print(f"Decision package written to: {pkg_path}")

    # Human approval gate (interactive)
    try:
        reviewer = input("Enter reviewer name: ").strip()
    except EOFError:
        reviewer = ""
    except KeyboardInterrupt:
        print("\nAborted.")
        return 0

    action = ""
    while action not in ("approve", "reject"):
        try:
            action = input("Approve or reject? (approve/reject): ").strip().lower()
        except EOFError:
            return 0
        except KeyboardInterrupt:
            print("\nAborted.")
            return 0

    reason = input("Reason (optional): ").strip() or None

    gate = ApprovalGate(audit_log_path=args.audit_log) if args.audit_log else ApprovalGate()
    try:
        if action == "approve":
            gate.approve(package, reviewer, reason)
            print(f"Approved by {reviewer}. Audit log updated.")
        else:
            gate.reject(package, reviewer, reason)
            print(f"Rejected by {reviewer}. Audit log updated.")
    except Exception as e:
        print(f"Approval failed: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
