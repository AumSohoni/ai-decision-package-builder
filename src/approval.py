from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from .models import ApprovalRecord, DecisionPackage


class ApprovalGate:
    def __init__(self, audit_log_path: str | Path | None = None):
        if audit_log_path is None:
            audit_log_path = Path(__file__).parent.parent / "audit_log.jsonl"
        self.audit_log_path = Path(audit_log_path)

    def approve(
        self,
        package: DecisionPackage,
        reviewer_name: str,
        reason: str | None = None,
    ) -> ApprovalRecord:
        if not reviewer_name or reviewer_name.strip() == "":
            raise ValueError("Reviewer name is required to approve/reject a package.")
        package.reviewer_name = reviewer_name.strip()
        package.reviewed_at = datetime.now(UTC)
        package.status = "approved"
        package.approval_reason = reason
        record = ApprovalRecord(
            package_id=package.package_id,
            risk_case_id=package.risk_case_id,
            reviewer_name=package.reviewer_name,
            action="approve",
            reason=reason,
        )
        self._write(record)
        return record

    def reject(
        self,
        package: DecisionPackage,
        reviewer_name: str,
        reason: str | None = None,
    ) -> ApprovalRecord:
        if not reviewer_name or reviewer_name.strip() == "":
            raise ValueError("Reviewer name is required to approve/reject a package.")
        package.reviewer_name = reviewer_name.strip()
        package.reviewed_at = datetime.now(UTC)
        package.status = "rejected"
        package.approval_reason = reason
        record = ApprovalRecord(
            package_id=package.package_id,
            risk_case_id=package.risk_case_id,
            reviewer_name=package.reviewer_name,
            action="reject",
            reason=reason,
        )
        self._write(record)
        return record

    def _write(self, record: ApprovalRecord) -> None:
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        line = record.model_dump_json()
        with self.audit_log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
