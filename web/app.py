import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError

from src.approval import ApprovalGate
from src.llm import provider_status
from src.models import DecisionPackage, RiskCase
from src.pipeline import analyze_risk_case
from src.retriever import Retriever

STATIC_DIR = Path(__file__).parent / "static"
DEFAULT_AUDIT_LOG = Path(__file__).parent.parent / "audit_log.jsonl"


class ReviewRequest(BaseModel):
    package_id: str
    reviewer_name: str
    action: str
    reason: str | None = None


def create_app(
    audit_log_path: str | Path | None = None,
    use_mock_llm: bool = True,
) -> FastAPI:
    app = FastAPI(title="Decision Desk", version="0.1.0")
    audit_path = Path(audit_log_path) if audit_log_path else DEFAULT_AUDIT_LOG
    app.state.packages: dict[str, DecisionPackage] = {}
    app.state.use_mock_llm = use_mock_llm
    app.state.audit_path = audit_path

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))

    @app.get("/api/past-decisions")
    def past_decisions() -> dict[str, Any]:
        return {"cases": Retriever().past_decisions}

    @app.get("/api/provider")
    def provider() -> dict[str, Any]:
        status = provider_status()
        status["default_mock"] = app.state.use_mock_llm
        return status

    @app.post("/api/analyze")
    def analyze(payload: dict[str, Any], use_mock: bool | None = None) -> dict[str, Any]:
        try:
            risk_case = RiskCase.model_validate(payload)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=json.loads(e.json())) from e

        mock = app.state.use_mock_llm if use_mock is None else use_mock
        try:
            analysis = analyze_risk_case(risk_case, use_mock_llm=mock)
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e)) from e

        app.state.packages[analysis.package.package_id] = analysis.package
        return {
            "risk_case": risk_case.model_dump(),
            "completeness_report": analysis.completeness_report.model_dump(),
            "similar_cases": [s.model_dump() for s in analysis.similar_cases],
            "package": analysis.package.model_dump(mode="json"),
            "used_mock": mock,
        }

    @app.post("/api/review")
    def review(req: ReviewRequest) -> dict[str, Any]:
        package = app.state.packages.get(req.package_id)
        if package is None:
            raise HTTPException(status_code=404, detail="Unknown package_id.")

        action = req.action.strip().lower()
        if action not in ("approve", "reject"):
            raise HTTPException(
                status_code=400, detail="action must be 'approve' or 'reject'."
            )

        gate = ApprovalGate(audit_log_path=audit_path)
        try:
            if action == "approve":
                record = gate.approve(package, req.reviewer_name, req.reason)
            else:
                record = gate.reject(package, req.reviewer_name, req.reason)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        return {
            "package": package.model_dump(mode="json"),
            "audit_entry": record.model_dump(mode="json"),
        }

    @app.get("/api/audit")
    def audit() -> dict[str, Any]:
        if not audit_path.exists():
            return {"entries": []}
        entries = []
        for line in audit_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                entries.append(json.loads(line))
        entries.reverse()
        return {"entries": entries}

    return app


app = create_app()
