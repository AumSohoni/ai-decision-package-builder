import json
import os
from pathlib import Path
from typing import Any, Dict, List

from .models import CompletenessReport, MissingField, RiskCase


class Checker:
    def __init__(self, checklist_path: str | Path | None = None):
        if checklist_path is None:
            checklist_path = Path(__file__).parent.parent / "data" / "checklist.json"
        self.checklist_path = Path(checklist_path)
        with self.checklist_path.open("r", encoding="utf-8") as f:
            self.checklist = json.load(f)

    def check(self, risk_case: RiskCase | Dict[str, Any]) -> CompletenessReport:
        if isinstance(risk_case, RiskCase):
            case_dict = risk_case.model_dump(exclude_none=True)
        else:
            case_dict = dict(risk_case)

        required = self.checklist.get("required", [])
        explain = self.checklist.get("explain", {})

        missing: List[MissingField] = []
        for field in required:
            if field not in case_dict or case_dict.get(field) in (None, "", []):
                missing.append(
                    MissingField(
                        field=field,
                        reason=explain.get(
                            field, f"Field '{field}' is required for a complete decision package."
                        ),
                    )
                )

        is_complete = len(missing) == 0
        completeness_score = int(round((len(required) - len(missing)) / len(required) * 100)) if required else 100
        notes = []
        if is_complete:
            notes.append("All required fields present.")
        else:
            notes.append(f"{len(missing)} required field(s) missing.")

        return CompletenessReport(
            is_complete=is_complete,
            missing=missing,
            completeness_score=completeness_score,
            notes=notes,
        )
