# AI Decision Package Builder

![CI](https://github.com/AumSohoni/ai-decision-package-builder/actions/workflows/ci.yml/badge.svg)

A tool that prepares a structured decision package for a human expert to review. The AI prepares, the human decides. This mirrors real-world risk governance: automation for preparation, accountability for approval.

## Problem statement
Risk management needs an AI-supported workflow where experts can review and assess risks asynchronously. The AI prepares structured decision packages combining completeness checks, expert perspectives, past decisions, and risk management best practices, keeping accountability with human stakeholders.

## Features
- **Risk case data model** (Pydantic) with `RiskCase` and `DecisionPackage`.
- **Completeness check (no AI)**: rule-based validation against a required-field checklist.
- **Similar-case retrieval**: TF-IDF + cosine similarity (scikit-learn) to surface the top 3 past decisions.
- **LLM generation with guardrails**: generates a JSON decision package, validates with Pydantic, retries once on invalid output, and only cites past case IDs that were retrieved.
- **Human approval gate**: requires a reviewer name, records approve/reject with timestamp and reason in an append-only audit log (`audit_log.jsonl`).
- **Deterministic tests**: LLM mocked; edge cases covered (incomplete inputs, non-existent cited IDs, missing reviewer).
- **CI**: GitHub Actions runs `ruff` and `pytest` on push/PR.

## Architecture
```text
Risk Case (JSON)
  -> Completeness Check (rules)
  -> Similar Case Retrieval (TF-IDF)
  -> LLM (JSON-only, citations restricted to retrieved IDs)
  -> Decision Package (draft)
  -> Human Approval (required reviewer + audit log)
```

### Data flow
1. Input `RiskCase` (JSON)
2. `checker.py` validates required fields from `data/checklist.json` -> `CompletenessReport`
3. `retriever.py` compares title+description+category against `data/past_decisions.json` -> top 3 `SimilarCase`
4. `llm.py` prompts the model to return JSON matching `DecisionPackage`; validates schema, enforces cited IDs are a subset of retrieved IDs, retries once
5. CLI writes the package to `out/decision_package_<id>.json` and prompts for approval
6. `approval.py` writes an append-only record to `audit_log.jsonl`; sets status `approved`/`rejected`

## What the AI does / does not do
**Does:**
- Summarize the risk case
- Flag missing required information and explain why it matters
- Retrieve and cite only known past decisions (no invention)
- Generate structured questions for experts
- Produce JSON that validates against the schema

**Does not:**
- Auto-approve risks
- Invent or hallucinate past case IDs (enforced)
- Override human judgment
- Commit secrets (keys loaded from environment only)

## Human accountability
- Approval/rejection **requires a reviewer name** (cannot be bypassed).
- Each decision is recorded in the append-only `audit_log.jsonl` with: `timestamp` (UTC), `package_id`, `risk_case_id`, `reviewer_name`, `action` (approve/reject), `reason`.
- `DecisionPackage` stores `reviewer_name`, `reviewed_at`, `approval_reason`, and `status` (`draft|approved|rejected`).
- Packages cannot be marked approved without a reviewer name.

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Unix
source .venv/bin/activate

pip install -r requirements.txt
```

## Environment variables
If using a real LLM (not mock):
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

Create a local `.env` (never committed); keys are read from the process environment.

## Usage

Run with a sample risk case (uses the mock LLM by default for a deterministic run):

```bash
python -m src.cli --input examples/sample.json --use-mock-llm
```

Or without the mock (requires an API key):

```bash
python -m src.cli --input examples/sample.json
```

Non-interactive (skips the prompts; useful for demos and CI):

```bash
python -m src.cli --input examples/sample.json --use-mock-llm --reviewer "Jane Doe" --action approve --reason "matches past case PD-008"
```

Outputs:
- `out/decision_package_RC-001.json` (status, reviewer, timestamp, and reason are written back after the review)
- An appended approval record in `audit_log.jsonl`

Example input: `examples/sample.json`. Mock data: `data/past_decisions.json` (15-20 fictional cases), `data/checklist.json`.

## Tests
```bash
pytest -q
```

Covers:
- Checker: complete, missing one, missing several
- Retriever: returns top 3, obvious match ranks first
- LLM: output validates; cited case IDs must exist in the retrieved set
- Approval: requires a reviewer name; writes audit log; sets approved/rejected
- CLI: non-interactive approve/reject persists status; no review leaves the package as a draft

## Lint
```bash
ruff check .
```

## CI
GitHub Actions workflow: `.github/workflows/ci.yml` runs `ruff check .` and `pytest -q` on push and PR. Badge:

```markdown
![CI](https://github.com/AumSohoni/ai-decision-package-builder/actions/workflows/ci.yml/badge.svg)
```

## Known limitations
- TF-IDF similarity is simple (no semantic embeddings yet)
- LLM retry is limited to 1 attempt
- Mock dataset is fictional and small
- A real run still needs an API key and network access

## Next steps
- Evaluation harness with 10 golden risk cases and a simple score tracked over time
- Switch to embeddings + vector store (FAISS/Chroma) for better retrieval
- Stronger JSON repair/guardrails and structured logging
- Export to PDF/Markdown for expert review
