# Flow
1. **Input**: Risk case JSON is loaded
2. **Completeness**: Rule-based check against checklist; report missing fields
3. **Retrieval**: TF-IDF ranks past decisions; return top 3
4. **Generation**: LLM produces DecisionPackage JSON (status=draft), restricted to retrieved IDs
5. **Validation**: Pydantic validates; retry once on failure; enforce citation whitelist
6. **Review**: Human provides reviewer name, action (approve/reject), reason
7. **Audit**: Append-only record written to udit_log.jsonl; package status updated
