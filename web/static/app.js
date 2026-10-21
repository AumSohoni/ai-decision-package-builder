const SAMPLE = {
  id: "RC-001",
  title: "API key exposure in logs",
  description: "API keys detected in application log files during a routine scan.",
  category: "data",
  severity: "high",
  owner: "alice",
  mitigation: "Rotate keys and redact logs.",
  impact: "high",
  likelihood: "medium",
  affected_assets: ["logging_service", "api_gateway"],
  reported_date: "2025-10-15",
  detection_method: "automated_scan",
};

const SECTIONS = ["intake", "analysis", "review", "audit"];
const STEP_ORDER = ["intake", "analysis", "review"];

const state = {
  section: "intake",
  package: null,
  report: null,
  similar: [],
  busy: false,
};

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const els = {
  panels: Object.fromEntries(
    SECTIONS.map((s) => [s, document.getElementById(`panel-${s}`)])
  ),
  nav: Object.fromEntries(
    $$(".rail-link").map((b) => [b.dataset.nav, b])
  ),
  steps: $$(".step"),
  statusChip: $("#status-chip"),
  reviewStatus: $("#review-status"),
  statusDot: $("#status-dot"),
  countSimilar: $("#count-similar"),
  countAudit: $("#count-audit"),
  form: $("#risk-form"),
  formError: $("#form-error"),
  analyzeBtn: $("#analyze-btn"),
  toReview: $("#to-review"),
  reviewer: $("#reviewer"),
  reason: $("#reason"),
  approveBtn: $("#approve-btn"),
  rejectBtn: $("#reject-btn"),
  reviewError: $("#review-error"),
  decisionBox: $("#decision-box"),
  stamp: $("#stamp"),
  stampMark: $("#stamp-mark"),
  stampTitle: $("#stamp-title"),
  stampMeta: $("#stamp-meta"),
  stampReason: $("#stamp-reason"),
  auditBody: $("#audit-body"),
  auditTable: $("#audit-table"),
  auditEmpty: $("#audit-empty"),
  live: $("#live-status"),
};

function announce(message) {
  els.live.textContent = "";
  window.setTimeout(() => {
    els.live.textContent = message;
  }, 30);
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function api(path, options) {
  const res = await fetch(path, options);
  let data = {};
  try {
    data = await res.json();
  } catch {
    data = {};
  }
  if (!res.ok) {
    let message = data.detail;
    if (Array.isArray(message)) {
      message = message.map((d) => d.msg || String(d)).join("; ");
    }
    throw new Error(message || `Request failed (${res.status})`);
  }
  return data;
}

function setStatus(status) {
  const label = status.charAt(0).toUpperCase() + status.slice(1);
  els.statusChip.textContent = label;
  els.statusChip.dataset.state = status;
  els.reviewStatus.textContent = label;
  els.reviewStatus.dataset.state = status;
  els.statusDot.hidden = status === "draft";
  els.statusDot.dataset.state = status;
}

function setStepState(section) {
  const index = STEP_ORDER.indexOf(section);
  els.steps.forEach((step) => {
    const name = step.dataset.step;
    const stepIndex = STEP_ORDER.indexOf(name);
    step.classList.remove("is-current", "is-done");
    if (section === "audit") {
      step.classList.add("is-done");
      return;
    }
    if (stepIndex === index) step.classList.add("is-current");
    else if (stepIndex < index) step.classList.add("is-done");
  });
}

function navigate(section) {
  if (!SECTIONS.includes(section)) return;
  state.section = section;

  SECTIONS.forEach((name) => {
    const panel = els.panels[name];
    panel.hidden = name !== section;
  });

  Object.entries(els.nav).forEach(([name, button]) => {
    button.classList.toggle("is-active", name === section);
  });

  setStepState(section);
  window.scrollTo({ top: 0, behavior: "auto" });

  const heading = els.panels[section]?.querySelector("h1, h2");
  if (heading) {
    heading.setAttribute("tabindex", "-1");
    heading.focus({ preventScroll: true });
  }

  if (section === "audit") refreshAudit();
}

function updateNavAvailability() {
  const hasPackage = Boolean(state.package);
  els.nav.analysis.disabled = !hasPackage;
  els.nav.review.disabled = !hasPackage;
}

/* ---------- Form ---------- */

function fillForm(data) {
  const form = els.form;
  form.elements.id.value = data.id || "";
  form.elements.title.value = data.title || "";
  form.elements.description.value = data.description || "";
  form.elements.category.value = data.category || "";
  form.elements.severity.value = data.severity || "";
  form.elements.owner.value = data.owner || "";
  form.elements.mitigation.value = data.mitigation || "";
  form.elements.impact.value = data.impact || "";
  form.elements.likelihood.value = data.likelihood || "";
  form.elements.affected_assets.value = (data.affected_assets || []).join(", ");
  form.elements.reported_date.value = data.reported_date || "";
  form.elements.detection_method.value = data.detection_method || "";
  els.formError.hidden = true;
}

function collectForm() {
  const f = els.form.elements;
  const assets = f.affected_assets.value
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  return {
    id: f.id.value.trim(),
    title: f.title.value.trim(),
    description: f.description.value.trim(),
    category: f.category.value,
    severity: f.severity.value,
    owner: f.owner.value.trim(),
    mitigation: f.mitigation.value.trim(),
    impact: f.impact.value.trim() || null,
    likelihood: f.likelihood.value.trim() || null,
    affected_assets: assets,
    reported_date: f.reported_date.value || null,
    detection_method: f.detection_method.value.trim() || null,
  };
}

function validate(payload) {
  const required = ["id", "title", "description", "category", "severity", "owner", "mitigation"];
  const missing = required.filter((key) => !payload[key]);
  const labels = {
    id: "Case ID",
    title: "Title",
    description: "Description",
    category: "Category",
    severity: "Severity",
    owner: "Owner",
    mitigation: "Proposed mitigation",
  };
  if (missing.length) {
    return `Fill in the required fields: ${missing.map((k) => labels[k]).join(", ")}.`;
  }
  return null;
}

async function onAnalyze(event) {
  event.preventDefault();
  if (state.busy) return;

  const payload = collectForm();
  const problem = validate(payload);
  if (problem) {
    showFormError(problem);
    return;
  }
  els.formError.hidden = true;
  state.busy = true;
  els.analyzeBtn.classList.add("is-loading");
  els.analyzeBtn.disabled = true;
  els.analyzeBtn.setAttribute("aria-busy", "true");
  announce("Analyzing risk case.");

  try {
    const data = await api("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.package = data.package;
    state.report = data.completeness_report;
    state.similar = data.similar_cases;
    renderAnalysis(data);
    updateNavAvailability();
    resetReview();
    navigate("analysis");
    animateMeter();
    announce("Analysis ready. Completeness and precedent shown.");
  } catch (err) {
    showFormError(err.message);
    announce("Analysis failed.");
  } finally {
    state.busy = false;
    els.analyzeBtn.classList.remove("is-loading");
    els.analyzeBtn.disabled = false;
    els.analyzeBtn.removeAttribute("aria-busy");
  }
}

function showFormError(message) {
  els.formError.textContent = message;
  els.formError.hidden = false;
}

/* ---------- Analysis render ---------- */

function renderAnalysis(data) {
  const report = data.completeness_report;
  const pkg = data.package;

  $("#package-tag").textContent = pkg.package_id;
  $("#score-value").textContent = report.completeness_score;

  const summary = $("#complete-summary");
  if (report.is_complete) {
    summary.textContent = "All checklist fields present. The package is ready for a human decision.";
  } else {
    const count = report.missing.length;
    summary.textContent = `${count} checklist ${count === 1 ? "field is" : "fields are"} missing. The package records them as open items, not blockers.`;
  }

  const bar = $("#score-bar");
  bar.style.transform = "scaleX(0)";
  bar.dataset.target = String(report.completeness_score);
  bar.dataset.level =
    report.completeness_score >= 100 ? "ok" : report.completeness_score >= 60 ? "warn" : "danger";

  const missingList = $("#missing-list");
  missingList.replaceChildren();
  report.missing.forEach((m) => {
    const li = el("li");
    li.append(el("span", "missing-field", m.field), el("span", "missing-reason", m.reason));
    missingList.append(li);
  });
  missingList.hidden = report.missing.length === 0;

  els.countSimilar.textContent = String(data.similar_cases.length);
  els.countSimilar.hidden = data.similar_cases.length === 0;
  $("#similar-note").textContent = `${data.similar_cases.length} retrieved`;

  const similar = $("#similar-list");
  similar.replaceChildren();
  data.similar_cases.forEach((c) => {
    const li = el("li", "similar-row");

    const id = el("span", "similar-id", c.id);

    const main = el("div", "similar-main");
    main.append(
      el("span", "similar-title", c.title),
      el("span", "similar-meta", `${c.category} · ${c.severity} · ${c.outcome}`)
    );

    const score = el("div", "similar-score");
    const track = el("span", "score-track");
    const fill = el("span");
    fill.style.width = `${Math.round(c.score * 100)}%`;
    track.append(fill);
    score.append(track, el("span", "score-num", c.score.toFixed(2)));

    li.append(id, main, score);
    similar.append(li);
  });

  $("#package-summary").textContent = pkg.summary;

  const info = $("#missing-info");
  info.replaceChildren();
  if (pkg.missing_information.length === 0) {
    info.append(el("li", "tag-none", "None — required fields complete."));
  } else {
    pkg.missing_information.forEach((field) => info.append(el("li", "", field)));
  }

  const questions = $("#questions");
  questions.replaceChildren();
  pkg.questions_for_experts.forEach((q) => questions.append(el("li", "", q)));
}

function animateMeter() {
  const bar = $("#score-bar");
  const target = Number(bar.dataset.target || 0);
  window.setTimeout(() => {
    bar.style.transform = `scaleX(${target / 100})`;
  }, 80);
}

/* ---------- Review ---------- */

function resetReview() {
  els.reviewer.value = "";
  els.reason.value = "";
  els.reviewError.hidden = true;
  els.stamp.hidden = true;
  els.decisionBox.hidden = false;
  setEditable(true);
  setStatus(state.package ? state.package.status : "draft");
}

function setEditable(editable) {
  els.reviewer.disabled = !editable;
  els.reason.disabled = !editable;
  els.approveBtn.disabled = !editable;
  els.rejectBtn.disabled = !editable;
}

async function submitDecision(action) {
  if (!state.package || state.busy) return;

  const reviewer = els.reviewer.value.trim();
  if (!reviewer) {
    els.reviewError.textContent = "Your name is required to record a decision.";
    els.reviewError.hidden = false;
    els.reviewer.focus();
    return;
  }

  els.reviewError.hidden = true;
  state.busy = true;
  setEditable(false);
  const button = action === "approve" ? els.approveBtn : els.rejectBtn;
  button.setAttribute("aria-busy", "true");
  announce(`Recording ${action}.`);

  try {
    const data = await api("/api/review", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        package_id: state.package.package_id,
        reviewer_name: reviewer,
        action,
        reason: els.reason.value.trim() || null,
      }),
    });

    state.package = data.package;
    renderStamp(data.audit_entry);
    setStatus(data.package.status);
    els.decisionBox.hidden = true;
    els.stamp.hidden = false;
    announce(`Package ${data.package.status}. Entry written to the audit log.`);
    await refreshAudit();
  } catch (err) {
    els.reviewError.textContent = err.message;
    els.reviewError.hidden = false;
    setEditable(true);
    announce("Decision was not recorded.");
  } finally {
    state.busy = false;
    button.removeAttribute("aria-busy");
  }
}

function renderStamp(entry) {
  const status = state.package.status;
  els.stamp.dataset.state = status;
  els.stampMark.textContent = status;
  els.stampTitle.textContent =
    status === "approved" ? "Package approved" : "Package rejected";

  const when = formatTimestamp(entry.timestamp);
  els.stampMeta.textContent = `${entry.reviewer_name} · ${when} · ${entry.package_id}`;

  if (entry.reason) {
    els.stampReason.textContent = `Reason: ${entry.reason}`;
    els.stampReason.hidden = false;
  } else {
    els.stampReason.hidden = true;
  }
}

/* ---------- Audit ---------- */

function formatTimestamp(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

async function refreshAudit() {
  try {
    const data = await api("/api/audit");
    renderAudit(data.entries);
  } catch (err) {
    els.auditEmpty.hidden = false;
    els.auditTable.hidden = true;
    els.auditEmpty.querySelector(".empty-title").textContent = "Audit log unavailable";
    els.auditEmpty.querySelector(".empty-body").textContent = err.message;
  }
}

function renderAudit(entries) {
  els.countAudit.textContent = String(entries.length);
  els.countAudit.hidden = entries.length === 0;

  if (entries.length === 0) {
    els.auditTable.hidden = true;
    els.auditEmpty.hidden = false;
    els.auditEmpty.querySelector(".empty-title").textContent = "No decisions recorded yet";
    els.auditEmpty.querySelector(".empty-body").textContent =
      "Approve or reject a package and the entry appears here. The log is append-only, so history is never rewritten.";
    return;
  }

  els.auditTable.hidden = false;
  els.auditEmpty.hidden = true;
  els.auditBody.replaceChildren();

  entries.forEach((entry) => {
    const tr = el("tr");
    const when = el("td", "cell-time", formatTimestamp(entry.timestamp));
    const pkg = el("td", "cell-id", entry.package_id);
    const reviewer = el("td", "", entry.reviewer_name);
    const action = el(
      "td",
      "cell-action",
      entry.action === "approve" ? "approved" : "rejected"
    );
    action.dataset.state = entry.action === "approve" ? "approved" : "rejected";
    const reason = el("td", "cell-reason", entry.reason || "—");
    tr.append(when, pkg, reviewer, action, reason);
    els.auditBody.append(tr);
  });
}

/* ---------- Reset ---------- */

function startNewReview() {
  state.package = null;
  state.report = null;
  state.similar = [];
  els.form.reset();
  els.formError.hidden = true;
  els.countSimilar.hidden = true;
  updateNavAvailability();
  resetReview();
  setStatus("draft");
  navigate("intake");
  const first = els.form.elements.id;
  if (first) first.focus();
  announce("Started a new review.");
}

/* ---------- Wiring ---------- */

Object.entries(els.nav).forEach(([name, button]) => {
  button.addEventListener("click", () => {
    if (button.disabled) return;
    navigate(name);
  });
});

els.form.addEventListener("submit", onAnalyze);
$("#load-sample").addEventListener("click", () => {
  fillForm(SAMPLE);
  els.formError.hidden = true;
  announce("Example risk case loaded.");
});

els.toReview.addEventListener("click", () => {
  navigate("review");
  els.reviewer.focus();
});

els.approveBtn.addEventListener("click", () => submitDecision("approve"));
els.rejectBtn.addEventListener("click", () => submitDecision("reject"));
$("#new-review").addEventListener("click", startNewReview);

updateNavAvailability();
refreshAudit();
