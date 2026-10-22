# PRODUCT.md

> Inferred from the repository, the brief, and the internship context. No live interview was run (no question mechanism in this session); assumptions are labeled and should be corrected by the owner.

## What this is

A risk-governance tool where AI prepares a structured decision package and a human expert reviews and decides. It exists to show a working, tested, honest implementation of "AI prepares, humans decide" — the pattern real risk teams need.

The project is an internship application artifact. It is judged on clarity, correct guardrails, and evidence of engineering care (tests, CI, an audit trail), against the kind of work a Swisscom IT risk-management team might do.

## Who it is for

- **Primary user (the reviewer):** a risk analyst or security officer who receives a prepared package and must make an accountable call. They are working through a queue, want the facts fast, and need to trust that nothing was invented.
- **Secondary user (the builder/reviewer of this repo):** a hiring team evaluating whether the author understands AI governance, not just model calls.

## Mode

**Operate.** The visitor is completing a task (review a risk, record a decision). Scanability, consistency, and trust outrank expression. Brand lives in precise details, not decoration.

## Job to be done

Given a messy, possibly incomplete risk report, produce a reviewable package that:
1. states what is missing and why it matters,
2. cites only real precedent,
3. asks the questions an expert should answer,
4. and never approves anything by itself.

## Success signals

- A stranger can run it offline (mock LLM) and complete the full loop in under a minute.
- Every approval in the audit log names a person, a time, and a reason.
- The AI's limits are visible in the UI, not buried in code.

## Product truths (constraints)

- The mock dataset is fictional; the UI states this rather than implying real history.
- Branding is neutral. This does not represent or affiliate with Swisscom or any employer.
- No secrets are stored; API keys come from the environment only.
- The audit log is append-only; history is never rewritten.
- A package cannot be approved without a named reviewer.

## Non-goals

- Auto-approval or autonomous action.
- Semantic embeddings or a vector store (TF-IDF is deliberate for the scope).
- Multi-tenant auth, roles, or persistence beyond a local JSONL log.

## Assumptions to confirm

- The intended audience above (risk analyst; hiring reviewer) is inferred, not stated.
- The tone ("dark operations console, not dashboard") was chosen for the use scene, not requested explicitly.
- Swisscom-neutral branding is an inference from the application context; confirm before any public use.
