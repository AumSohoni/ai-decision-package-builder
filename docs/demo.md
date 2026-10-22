# Two-minute demo

A script for showing the console to a reviewer. Total: ~120 seconds.

Prep once, before anyone is watching:

```bash
python -m uvicorn web.app:app --reload
```

Open http://127.0.0.1:8000 and confirm the header shows the engine you want
(mock for a guaranteed offline run, Gemini if `.env` has a key). Delete
`audit_log.jsonl` first if you want the audit log to start empty.

---

**0:00 - 0:15 — Frame it**

> "Risk teams get messy, incomplete reports and have to decide anyway. This
> tool prepares the decision package; a named human still makes the call.
> Watch what it does with a report that is missing things."

**0:15 - 0:30 — Intake**

Click **Load example**. The form fills with the RC-001 API-key-exposure case.
Leave the header engine on **mock** for the first pass so the timing is
predictable. Point at the engine readout and say the model is one toggle away.

**0:30 - 0:50 — Analysis: completeness**

Click **Run analysis**. Land on the analysis view.

> "The completeness check is deterministic, no model involved. The sample
> scores 100 because every checklist field is filled. The whole point is the
> gap it surfaces when fields are missing."

To show the gap live: go back to intake, clear **Impact**, **Likelihood**, and
**Affected assets** (the form does not hard-require these, but the checklist
does), then analyze again. The score drops, the missing list appears, and each
row names the field and why it matters.

**0:50 - 1:10 — Analysis: precedent and draft**

Scroll to **Similar past decisions**.

> "It retrieves the three closest cases from twenty by TF-IDF and cites only
> those. The model is not allowed to invent a case ID; if it does, the package
> fails validation and retries."

Point at the draft summary and the two expert questions. If the engine is on
Gemini, the readout strip shows the latency (about two seconds) and the draft
text is freshly generated.

**1:10 - 1:30 — Review**

Click **Continue to decision**. Click **Approve** with the name field empty:
the console refuses and points at the field.

> "Approval is gated on a reviewer name. There is no path around it."

Type a name and a reason, approve. The stamp lands with the name, UTC
timestamp, package ID, and reason.

**1:30 - 1:45 — Audit**

Click **Audit log**. The decision is at the top: time, package, reviewer,
action, reason.

> "Append-only. History is never rewritten. That is the accountability half."

**1:45 - 2:00 — Close**

> "The CLI runs the same pipeline headless for CI and batch use. Tests are
> deterministic against the mock, and the real Gemini path is wired behind the
> same interface. The AI prepares, the human decides."

---

## Optional: show the real model

Flip the header toggle to **real AI**, analyze again, and point at the latency
and the changed wording. Requires a key in `.env`; see the README.

## Failure lines, if something breaks

- Blank analysis view: check the browser console. The API returns 502 when the
  real provider fails after retries; the message shows in the form error area.
- Gemini 503: aliases are occasionally overloaded. The client falls back across
  a list of models before giving up. Re-run the request.
