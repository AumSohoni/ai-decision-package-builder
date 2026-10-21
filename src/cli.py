from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .approval import ApprovalGate
from .models import DecisionPackage, RiskCase
from .pipeline import analyze_risk_case


def load_risk_case(path: str | Path) -> RiskCase:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    return RiskCase.model_validate(data)


def normalize_action(value: str) -> str:
    value = value.strip().lower()
    if value in ("approve", "approved", "a"):
        return "approve"
    if value in ("reject", "rejected", "r"):
        return "reject"
    raise ValueError(f"Invalid action: {value!r}. Use 'approve' or 'reject'.")


def resolve_review(args: argparse.Namespace) -> tuple[str, str, str | None] | None:
    """Resolve the human review decision.

    Returns (reviewer, action, reason) or None if the user aborted.
    When --reviewer and --action are both supplied, runs fully non-interactive.
    """
    reviewer = (args.reviewer or "").strip()
    action = normalize_action(args.action) if args.action else ""
    reason = args.reason

    if reviewer and action:
        return reviewer, action, reason

    try:
        if not reviewer:
            reviewer = input("Enter reviewer name: ").strip()
        while action not in ("approve", "reject"):
            action = normalize_action(
                input("Approve or reject? (approve/reject): ")
            )
        if reason is None:
            reason = input("Reason (optional): ").strip() or None
    except EOFError:
        return None
    except KeyboardInterrupt:
        print("\nAborted.")
        return None

    return reviewer, action, reason


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
    parser.add_argument(
        "--reviewer",
        default=None,
        help="Reviewer name (with --action runs non-interactively)",
    )
    parser.add_argument(
        "--action",
        default=None,
        choices=["approve", "reject"],
        help="Decision to apply without prompting",
    )
    parser.add_argument("--reason", default=None, help="Reason for the decision")
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        risk_case = load_risk_case(args.input)
    except Exception as e:
        print(f"Failed to load risk case: {e}", file=sys.stderr)
        return 1

    try:
        analysis = analyze_risk_case(risk_case, use_mock_llm=args.use_mock_llm)
    except Exception as e:
        print(f"Failed to generate decision package: {e}", file=sys.stderr)
        return 1

    package = analysis.package

    pkg_path = out_dir / f"decision_package_{risk_case.id}.json"
    _write_package(pkg_path, package)
    print(f"Decision package written to: {pkg_path}")

    decision = resolve_review(args)
    if decision is None:
        print("No review recorded; package remains a draft.", file=sys.stderr)
        return 0

    reviewer, action, reason = decision
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

    _write_package(pkg_path, package)
    print(f"Package status updated to '{package.status}' in: {pkg_path}")

    return 0


def _write_package(path: Path, package: DecisionPackage) -> None:
    with path.open("w", encoding="utf-8") as f:
        f.write(package.model_dump_json(indent=2))


if __name__ == "__main__":
    sys.exit(main())
