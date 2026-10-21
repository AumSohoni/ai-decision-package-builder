# Flow

Steps 2-4 are shared by both surfaces through `src/pipeline.py` (`analyze_risk_case`); the CLI and the web console only differ in how they collect input and present the result.

1. **Input**: Risk case JSON is loaded (`examples/sample.json`), entered in the CLI, or filled in the web intake form.
2. **Completeness**: Rule-based check against `data/checklist.json`; report missing fields and why they matter.
3. **Retrieval**: TF-IDF ranks past decisions from `data/past_decisions.json`; return the top 3.
4. **Generation**: LLM produces a `DecisionPackage` JSON (status=draft), restricted to retrieved case IDs.
5. **Validation**: Pydantic validates the output; retry once on failure; enforce the citation whitelist.
6. **Review**: A human provides a reviewer name, an action (approve/reject), and an optional reason. This can be interactive, passed as CLI flags (`--reviewer`, `--action`, `--reason`), or submitted from the web review step.
7. **Audit**: An append-only record is written to `audit_log.jsonl`; the package status is updated (written back to the output file by the CLI, and returned to the browser with a stamp by the web console). The web audit view reads this log newest-first.

## Guardrails
- The model may only cite past case IDs that were retrieved.
- A package cannot be approved or rejected without a reviewer name.
- Approvals/rejections are recorded with a UTC timestamp.
