from __future__ import annotations

import uuid
from dataclasses import dataclass

from .checker import Checker
from .llm import LLM, FakeLLMClient, build_llm
from .models import CompletenessReport, DecisionPackage, RiskCase, SimilarCase
from .retriever import Retriever


@dataclass
class Analysis:
    risk_case: RiskCase
    completeness_report: CompletenessReport
    similar_cases: list[SimilarCase]
    package: DecisionPackage


def build_mock_package_dict(
    risk_case: RiskCase,
    completeness_report: CompletenessReport,
    similar_cases: list[SimilarCase],
) -> dict:
    retrieved_ids = {s.id for s in similar_cases}
    return {
        "package_id": f"PKG-{uuid.uuid4().hex[:8].upper()}",
        "risk_case_id": risk_case.id,
        "summary": f"Summary for {risk_case.title}.",
        "completeness_report": completeness_report.model_dump(),
        "missing_information": [m.field for m in completeness_report.missing],
        "similar_cases": [s.model_dump() for s in similar_cases if s.id in retrieved_ids],
        "questions_for_experts": [
            "Is the proposed mitigation sufficient given severity?",
            "Are there additional affected assets to consider?",
        ],
        "status": "draft",
    }


def analyze_risk_case(
    risk_case: RiskCase,
    use_mock_llm: bool = True,
    llm: LLM | None = None,
    model: str | None = None,
) -> Analysis:
    checker = Checker()
    completeness_report = checker.check(risk_case)

    retriever = Retriever()
    similar_cases = retriever.retrieve(risk_case, top_k=3)

    if llm is None:
        if use_mock_llm:
            mock = build_mock_package_dict(risk_case, completeness_report, similar_cases)
            llm = LLM(client=FakeLLMClient(mock))
        else:
            llm = build_llm(use_mock=False, model=model)

    package = llm.generate_package(risk_case, completeness_report, similar_cases)
    return Analysis(
        risk_case=risk_case,
        completeness_report=completeness_report,
        similar_cases=similar_cases,
        package=package,
    )
