import io
import json
import urllib.error

import pytest

from src.llm import GeminiClient, build_llm
from src.models import CompletenessReport, DecisionPackage, RiskCase, SimilarCase


def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url="https://example.test",
        code=code,
        msg="error",
        hdrs=None,  # type: ignore[arg-type]
        fp=io.BytesIO(b'{"error": {"message": "busy"}}'),
    )


def _ok_response(text: str) -> str:
    return json.dumps({"candidates": [{"content": {"parts": [{"text": text}]}}]})


def test_gemini_requires_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        GeminiClient(api_key=None)


@pytest.mark.filterwarnings("ignore::ResourceWarning")
@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
def test_gemini_falls_back_when_model_overloaded(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    client = GeminiClient()
    client.models = ["busy-model", "healthy-model"]

    calls = []

    def fake_post(model, prompt):
        calls.append(model)
        if model == "busy-model":
            raise _http_error(503)
        return _ok_response('{"ok": true}')

    monkeypatch.setattr(client, "_post", fake_post)
    assert client.generate("hi") == '{"ok": true}'
    assert client.model == "healthy-model"
    assert calls[0] == "busy-model"


@pytest.mark.filterwarnings("ignore::ResourceWarning")
@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
def test_gemini_retries_then_raises_when_all_fail(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    client = GeminiClient()
    client.models = ["a", "b"]

    def fake_post(model, prompt):
        raise _http_error(503)

    monkeypatch.setattr(client, "_post", fake_post)
    with pytest.raises(RuntimeError):
        client.generate("hi")


def test_prompt_guards_shape_and_citations(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    client = GeminiClient()
    client.models = ["m"]
    captured = {}

    def fake_post(model, prompt):
        captured["prompt"] = prompt
        return _ok_response(
            json.dumps(
                {
                    "package_id": "PKG-1",
                    "risk_case_id": "RC-001",
                    "summary": "s",
                    "completeness_report": {
                        "is_complete": True,
                        "missing": [],
                        "completeness_score": 100,
                        "notes": [],
                    },
                    "missing_information": [],
                    "similar_cases": [],
                    "questions_for_experts": ["q"],
                    "status": "draft",
                }
            )
        )

    monkeypatch.setattr(client, "_post", fake_post)

    from src.llm import LLM

    llm = LLM(client=client)
    risk = RiskCase(
        id="RC-001",
        title="t",
        description="d",
        category="data",
        severity="high",
        owner="o",
        mitigation="m",
    )
    report = CompletenessReport(is_complete=True, missing=[], completeness_score=100)
    similar = [
        SimilarCase(
            id="PD-008",
            title="past",
            category="data",
            severity="high",
            outcome="approved",
            reasoning="similar",
            score=0.5,
        )
    ]
    package = llm.generate_package(risk, report, similar)
    assert isinstance(package, DecisionPackage)
    assert "output_example" in captured["prompt"]
    assert "PD-008" in captured["prompt"]


def test_build_llm_mock_is_offline():
    llm = build_llm(use_mock=True)
    assert llm.client is not None
    assert hasattr(llm.client, "generate")
