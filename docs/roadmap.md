# Roadmap

Goal: a working, well-tested tool where a stranger can clone the repo, run one command, see a decision package generated from sample input, approve it, and see the audit log entry.

Status legend: [x] done in scaffold, [ ] to do.

## Day 1 - Repo setup and data models
- [x] Repo structure (`src/`, `tests/`, `data/`, `docs/`), `.gitignore`, `requirements.txt`
- [x] `RiskCase`, `DecisionPackage`, `CompletenessReport`, `SimilarCase`, `ApprovalRecord`
- [x] `Status` enum (draft/approved/rejected) + reviewer name/timestamp fields
- [ ] Review the models and adjust fields to your own judgment

## Day 2 - Mock data and completeness check
- [x] `data/past_decisions.json` (20 fictional decisions with outcomes and reasoning)
- [x] `data/checklist.json` (required fields + why each matters)
- [x] `src/checker.py` rule-based completeness check
- [x] Tests: complete, missing one, missing several
- [ ] Expand/flavor the mock data; make the reasoning realistic

## Day 3 - Similar-case retrieval
- [x] `src/retriever.py` TF-IDF + cosine similarity, top 3
- [x] Test: returns top 3; obvious match ranks first
- [ ] (Stretch) swap TF-IDF for embeddings

## Day 4 - LLM step with guardrails
- [x] `src/llm.py` prompt, JSON-only output, Pydantic validation, retry once
- [x] Enforce: cited IDs must be in the retrieved set
- [x] `FakeLLMClient` for deterministic tests
- [ ] Try the real API with your key; tune the prompt

## Day 5 - Approval gate and CLI
- [x] `src/approval.py` approve/reject, requires reviewer name, append-only `audit_log.jsonl`
- [x] `src/cli.py` end-to-end flow
- [x] Tests: approval cannot bypass reviewer; audit log written
- [x] Non-interactive flags (`--reviewer`, `--action`, `--reason`)
- [x] Package file re-written after the review so status/reviewer persist

## Day 6 - CI and README
- [x] `.github/workflows/ci.yml` (ruff + pytest on push/PR)
- [x] README with problem, flow, guardrails, limitations, next steps
- [ ] Confirm the CI run is green and the badge shows

## Day 7 - Buffer / polish
- [ ] Fix anything red in CI
- [ ] Tighten README wording (this is what reviewers read first)
- [ ] (Stretch) evaluation harness: 10 golden cases + tracked score

## Day 8 - Web console
- [x] `src/pipeline.py` shared `analyze_risk_case` so CLI and web stay in sync
- [x] `web/app.py` FastAPI endpoints: past decisions, analyze, review, audit
- [x] Single-page console (`web/static/`) with intake, analysis, review, and audit views
- [x] `tests/test_web.py` covers the endpoints with an isolated audit log
- [ ] (Stretch) persist packages to a store instead of in-memory
- [ ] (Stretch) stream the LLM response instead of a single request

## Stretch - Evaluation harness
- [ ] `eval/golden_cases.json` with expected properties
- [ ] Runner that calls the real model and scores results
- [ ] Commit a score history to show QA applied to an AI system

## Definition of done
A stranger can clone the repo, run one command (`python -m src.cli --input examples/sample.json --use-mock-llm`) or one server (`uvicorn web.app:app`), see a decision package generated from sample input, approve it, and see the audit log entry.
