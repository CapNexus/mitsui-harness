"use strict";

const S = { overview: null, story: null, tab: "story", filter: "all", run: null, es: null, threshold: 80 };
const $ = (sel, el = document) => el.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmt = (n) => (n >= 1000 ? (n / 1000).toFixed(n >= 100000 ? 0 : 1) + "k" : String(n || 0));
const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* storage unavailable */ } },
};

async function api(path, opts = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || res.statusText);
  return body;
}
function toast(msg, ms = 5000) {
  const t = $("#toast"); t.textContent = msg; t.classList.remove("hidden");
  clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.add("hidden"), ms);
}
function md(text) {
  const body = text.replace(/^---[\s\S]*?\n---\s*\n/, "");
  return window.marked ? window.marked.parse(body) : `<pre>${esc(body)}</pre>`;
}
const confClass = (c) => (c == null ? "" : c >= S.threshold ? "hi" : "lo");

// --- overview ------------------------------------------------------------------------------

async function loadOverview() {
  const [ov, env] = await Promise.all([api("/api/overview"), api("/api/environment")]);
  S.overview = ov; S.threshold = ov.threshold;
  renderEnv(env); renderTokens(ov.tokens); renderNext(); renderTree();
}

function renderEnv(env) {
  const b = (ok, label, title) => `<span class="badge ${ok ? "ok" : "bad"}" title="${esc(title)}">${ok ? "✓" : "✗"} ${label}</span>`;
  $("#env").innerHTML =
    b(!!env.kiro_cli, "kiro-cli", env.kiro_cli || "not on PATH") +
    b(env.auto_approve, "AEW_AUTO_APPROVE", "required to implement; analysis works without it") +
    b(!!env.npm, "npm", env.npm || "needed by the code-repo validator") +
    (env.parent_dirty.length ? `<span class="badge warn" title="${esc(env.parent_dirty.join("\n"))}">parent repo has ${env.parent_dirty.length} uncommitted change(s)</span>` : "");
}

function renderTokens(t) {
  const a = t.analysis.input + t.analysis.output, i = t.implementation.input + t.implementation.output;
  const est = t.any_reported ? "" : " est.";
  $("#tokens").innerHTML = `<span class="badge">Analysis ~${fmt(a)} tok${est}</span><span class="badge">Implementation ~${fmt(i)} tok${est}</span>`;
}

function renderNext() {
  const ov = S.overview, el = $("#next");
  const s = ov.stories.find((x) => x.id === ov.next);
  if (!s) { el.innerHTML = `<h3>Suggested next</h3><p class="muted small">${esc(ov.next_reason)}</p>`; return; }
  el.innerHTML = `<h3>Suggested next story</h3>
    <div class="sid">${esc(s.id)} · ${esc(s.repo)}</div>
    <div class="title">${esc(s.title)}</div>
    <div class="muted small">${esc(ov.next_reason)}</div>
    <div class="row">${s.confidence != null ? `<span class="conf ${confClass(s.confidence)}">confidence ${s.confidence}%</span>` : '<span class="muted small">not analyzed yet</span>'}
    <button class="btn primary" id="openNext">Open</button></div>`;
  $("#openNext").onclick = () => openStory(s.id, "analysis");
}

function matches(s) {
  const q = $("#search").value.trim().toLowerCase();
  if (q && !(s.id.toLowerCase().includes(q) || s.title.toLowerCase().includes(q))) return false;
  if (S.filter === "all") return true;
  if (S.filter === "blocked") return s.state === "blocked" || s.state === "human";
  return s.state === S.filter;
}

function renderTree() {
  const ov = S.overview, open = new Set(JSON.parse(store.get("openFeatures") || "[]"));
  $("#tree").innerHTML = ov.features.map((f) => {
    const rows = ov.stories.filter((s) => s.feature_folder === f.folder && matches(s));
    const all = ov.stories.filter((s) => s.feature_folder === f.folder);
    if (!rows.length && S.filter !== "all") return "";
    const done = all.filter((s) => s.state === "done").length;
    return `<details data-f="${esc(f.folder)}" ${open.has(f.folder) || rows.some((r) => r.id === ov.next) ? "open" : ""}>
      <summary><span class="sid">${esc(f.id)}</span> ${esc(f.title)}<span class="count">${done}/${all.length}</span></summary>
      ${rows.map((s) => `<div class="srow ${S.story?.summary.id === s.id ? "sel" : ""}" data-id="${esc(s.id)}" title="${esc(s.title)}">
        <span class="sid">${esc(s.id)}</span><span class="t">${esc(s.title)}</span>
        <span>${s.confidence != null ? `<span class="conf ${confClass(s.confidence)}">${s.confidence}%</span> ` : ""}<span class="state ${esc(s.state)}">${s.id === ov.next ? "next" : esc(s.state)}</span></span>
      </div>`).join("")}
    </details>`;
  }).join("") || '<p class="muted small">No stories match.</p>';
  $("#tree").querySelectorAll(".srow").forEach((r) => (r.onclick = () => openStory(r.dataset.id)));
  $("#tree").querySelectorAll("details").forEach((d) => d.addEventListener("toggle", () => {
    const ids = [...$("#tree").querySelectorAll("details[open]")].map((x) => x.dataset.f);
    store.set("openFeatures", JSON.stringify(ids));
  }));
}

// --- story -----------------------------------------------------------------------------------

async function openStory(id, tab) {
  S.story = await api(`/api/stories/${encodeURIComponent(id)}`);
  if (tab) S.tab = tab;
  store.set("story", id);
  renderTree(); renderStory();
}

function renderStory() {
  const st = S.story, s = st.summary;
  const chip = (k, v) => (v ? `<span class="badge" title="${k}">${esc(k)}: ${esc(v)}</span>` : "");
  const tabs = [["story", "Story"], ["readiness", "Readiness"], ["analysis", "Analysis & confidence"], ["implement", "Implement"], ["runs", `Runs (${st.runs.length})`]];
  $("#story").innerHTML = `<header><span class="sid">${esc(s.id)}</span><h2>${esc(s.title)}</h2>
      <span class="state ${esc(s.state)}">${st.is_next ? "suggested next" : esc(s.state)}</span></header>
    <div class="meta">${chip("status", s.status)}${chip("tier", s.tier)}${chip("executor", s.executor)}${chip("repo", s.repo)}${chip("owner", s.owner)}${chip("due", s.due)}
      <span class="badge" title="tokens for this story">~${fmt(st.tokens.analysis.input + st.tokens.analysis.output + st.tokens.implementation.input + st.tokens.implementation.output)} tok${st.tokens.any_reported ? "" : " est."}</span></div>
    <nav class="tabs">${tabs.map(([k, l]) => `<button class="tab ${S.tab === k ? "on" : ""}" data-tab="${k}">${l}</button>`).join("")}</nav>
    <div id="tabbody"></div>`;
  $("#story").querySelectorAll(".tab").forEach((b) => (b.onclick = () => { S.tab = b.dataset.tab; renderStory(); }));
  ({ story: tabStory, readiness: tabReadiness, analysis: tabAnalysis, implement: tabImplement, runs: tabRuns })[S.tab]();
}

function tabStory() {
  const st = S.story;
  const deps = st.dependencies.length ? `<h4>Blocked by</h4><ul>${st.dependencies.map((d) => `<li><b>${esc(d.id)}</b> ${esc(d.what || "")} — type ${esc(d.type || "?")}, <i>${esc(d.status)}</i>${d.owner ? `, owner ${esc(d.owner)}` : ""}</li>`).join("")}</ul>` : "";
  const wait = st.summary.waiting_on.length ? `<p class="errors">Waiting on unfinished stories: ${st.summary.waiting_on.map(esc).join(", ")}</p>` : "";
  $("#tabbody").innerHTML = `${wait}${deps}<div class="md">${md(st.text)}</div><p class="muted small">${esc(st.summary.path)}</p>`;
}

function factorList(factors) {
  return `<ul class="factors">${factors.map((f) => `<li class="lv-${esc(f.level)}"><b>${esc(f.name)}</b>${f.weight ? ` <span class="muted small">(weight ${f.weight})</span>` : ""}: ${esc(f.detail)}</li>`).join("")}</ul>`;
}

function tabReadiness() {
  const r = S.story.readiness;
  $("#tabbody").innerHTML = `<p>Deterministic readiness: <b>${r.score}%</b>${r.cap < 100 ? ` · confidence is capped at <b>${r.cap}%</b> until the blocking items are cleared` : ""}.</p>
    ${factorList(r.factors)}
    <p class="muted small">These facts come from the story front-matter, the dependency register and config/parameters.md. They make up 40% of the confidence score; the Kiro analysis makes up 60%.</p>`;
}

function latest(kind) { return S.story.runs.find((r) => r.kind === kind); }

function tabAnalysis() {
  const a = latest("analysis"), body = $("#tabbody");
  const running = a && ["queued", "running"].includes(a.status);
  let html = `<div class="row"><button class="btn primary" id="btnAnalyze" ${running || S.overview.active_run ? "disabled" : ""}>${a ? "Re-run analysis" : "Run analysis"}</button>
    <span class="muted small">Kiro's read-only reviewer reads the story, ADRs, knowledge, task-list context and steering, then scores readiness. ${S.threshold}% or more is a good start.</span></div>`;
  if (a) {
    html += `<p class="muted small">Latest: <a href="#" data-run="${esc(a.id)}">${esc(a.id)}</a> · ${esc(a.status)} · ${esc(a.updated_at)}</p>`;
    if (a.status === "failed") html += `<p class="errors">${esc(a.error)}</p>`;
  }
  const r = a?.result;
  if (r) {
    const c = r.confidence, color = c >= S.threshold ? "var(--ok)" : c >= 60 ? "var(--warn)" : "var(--bad)";
    const dims = Object.entries(r.dimensions || {});
    html += `<div class="gauge"><div class="dial" style="background: conic-gradient(${color} ${c * 3.6}deg, var(--chip) 0)"><span>${c}%</span></div>
      <div class="bars">${dims.map(([k, v]) => `<span>${esc(k.replace(/_/g, " "))}</span><span class="bar"><i style="width:${Number(v)}%"></i></span><span>${Number(v)}</span>`).join("")}
      <span>agent score</span><span class="bar"><i style="width:${r.agent}%"></i></span><span>${r.agent}</span>
      <span>readiness</span><span class="bar"><i style="width:${r.readiness}%"></i></span><span>${r.readiness}</span></div></div>
      <p>${c >= S.threshold ? `<span class="okbox">Ready to start (${c}% ≥ ${S.threshold}%).</span>` : `<span class="errors">Below ${S.threshold}%${r.cap < 100 ? `; capped at ${r.cap}% by readiness` : ""}. Resolve the risks or give a reason to override.</span>`} Recommendation: <b>${esc(r.recommendation || "")}</b></p>
      <p>${esc(r.summary || "")}</p>
      ${r.risks?.length ? `<h4>Risks</h4><ul>${r.risks.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : ""}
      ${r.questions?.length ? `<h4>Questions for a human</h4><ul>${r.questions.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : ""}
      ${r.relevant_docs?.length ? `<h4>Documents that matter</h4><ul>${r.relevant_docs.map((x) => `<li><code>${esc(x)}</code></li>`).join("")}</ul>` : ""}
      <div class="row"><button class="btn primary" id="goImpl">Continue to implement →</button></div>`;
  }
  body.innerHTML = html;
  $("#btnAnalyze").onclick = async () => {
    try { const { run_id } = await api(`/api/stories/${S.story.summary.id}/analyze`, { method: "POST" }); await openRun(run_id); await refreshStory(); }
    catch (e) { toast(e.message); }
  };
  body.querySelectorAll("[data-run]").forEach((x) => (x.onclick = (ev) => { ev.preventDefault(); openRun(x.dataset.run); }));
  const go = $("#goImpl"); if (go) go.onclick = () => { S.tab = "implement"; renderStory(); };
}

function tabImplement() {
  const st = S.story, a = latest("analysis"), conf = a?.status === "completed" ? a.confidence : null;
  const impl = latest("implementation");
  const low = conf == null || conf < S.threshold;
  $("#tabbody").innerHTML = `
    ${impl && !["completed", "rejected"].includes(impl.status) ? `<p class="errors">An implementation run exists: <a href="#" data-run="${esc(impl.id)}">${esc(impl.id)}</a> (${esc(impl.status)}). Open it to resume or review.</p>` : ""}
    <p>Confidence: ${conf == null ? '<b>not analyzed</b> — run the analysis first' : `<span class="conf ${confClass(conf)}">${conf}%</span>`}</p>
    <div class="field"><label for="branch">Branch (suggested from the story id; all changes go here)</label>
      <input type="text" id="branch" value="${esc(st.branch_suggestion)}"></div>
    <label class="row"><input type="checkbox" id="scaffold"> Scaffold unlock — first code story in this submodule may ADD toolchain configs (F02-S02, F04-S04)</label>
    <div class="field ${low && conf != null ? "" : "hidden"}"><label for="override">Reason to start below ${S.threshold}% (recorded in harness-db)</label>
      <textarea id="override" rows="2"></textarea></div>
    <div class="row"><button class="btn" id="btnPre">Check preflight</button><button class="btn primary" id="btnStart">Start implementation</button></div>
    <div id="pre"></div>
    <p class="muted small">Runs the harness plan_build loop with Kiro: classify → plan → plan_exists → write_tests → red → implement → tests_unchanged → green → validate → review → <b>human review</b>. The agent never commits; you review the diff and commit at the end.</p>`;
  const body = () => ({ branch: $("#branch").value.trim(), scaffold: $("#scaffold").checked, override_reason: $("#override").value });
  $("#btnPre").onclick = async () => {
    const r = await api(`/api/stories/${st.summary.id}/preflight`, { method: "POST", body: JSON.stringify(body()) });
    $("#pre").innerHTML = r.ok ? '<p class="okbox">Preflight passed.</p>' : `<div class="errors">${r.errors.map(esc).join("\n")}</div>`;
  };
  $("#btnStart").onclick = async () => {
    try { const { run_id } = await api(`/api/stories/${st.summary.id}/implement`, { method: "POST", body: JSON.stringify(body()) }); await openRun(run_id); await refreshStory(); }
    catch (e) { $("#pre").innerHTML = `<div class="errors">${esc(e.message)}</div>`; }
  };
  $("#tabbody").querySelectorAll("[data-run]").forEach((x) => (x.onclick = (ev) => { ev.preventDefault(); openRun(x.dataset.run); }));
}

function tabRuns() {
  const runs = S.story.runs;
  $("#tabbody").innerHTML = runs.length ? `<div class="md"><table><thead><tr><th>Run</th><th>Kind</th><th>Status</th><th>Branch</th><th>Confidence</th><th>Updated</th></tr></thead><tbody>
    ${runs.map((r) => `<tr><td><a href="#" data-run="${esc(r.id)}">${esc(r.id)}</a></td><td>${esc(r.kind)}</td><td>${esc(r.status)}</td><td>${esc(r.branch || "")}</td><td>${r.confidence ?? ""}</td><td>${esc(r.updated_at)}</td></tr>`).join("")}
    </tbody></table></div>` : '<p class="muted">No runs yet.</p>';
  $("#tabbody").querySelectorAll("[data-run]").forEach((x) => (x.onclick = (ev) => { ev.preventDefault(); openRun(x.dataset.run); }));
}

async function refreshStory() { if (S.story) { const id = S.story.summary.id; S.story = await api(`/api/stories/${id}`); renderStory(); } }

// --- run panel and console -------------------------------------------------------------------

async function openRun(rid) {
  if (S.es) { S.es.close(); S.es = null; }
  $("#runpanel").classList.remove("hidden");
  $("#console").innerHTML = "";
  S.run = rid; store.set("run", rid);
  await refreshRun();
  const es = new EventSource(`/api/runs/${encodeURIComponent(rid)}/events`);
  es.addEventListener("line", (ev) => appendLine(JSON.parse(ev.data)));
  es.addEventListener("status", () => refreshRun());
  S.es = es;
  $("#runpanel").scrollIntoView({ behavior: "smooth", block: "start" });
}

const ALWAYS = new Set(["phase", "step", "check", "warn", "error"]);
function visible(kind) {
  if (ALWAYS.has(kind)) return true;
  const box = document.querySelector(`.consolebar input[data-kind="${kind}"]`);
  return box ? box.checked : true;
}
function appendLine(e) {
  const c = $("#console"), div = document.createElement("div");
  div.className = `ln k-${e.kind}`; div.dataset.kind = e.kind;
  div.innerHTML = `<span class="ts">${esc(e.ts.slice(11, 19))}</span> ${e.step ? `<span class="st">[${esc(e.step)}]</span> ` : ""}${esc(e.text)}`;
  if (!visible(e.kind)) div.classList.add("hidden");
  c.appendChild(div);
  if (c.childElementCount > 5000) c.firstElementChild.remove();
  if ($("#follow").checked) c.scrollTop = c.scrollHeight;
}
document.addEventListener("change", (ev) => {
  const k = ev.target.dataset?.kind; if (!k) return;
  document.querySelectorAll(`#console .ln[data-kind="${k}"]`).forEach((d) => d.classList.toggle("hidden", !ev.target.checked));
});

async function refreshRun() {
  if (!S.run) return;
  const r = await api(`/api/runs/${encodeURIComponent(S.run)}`);
  const totalIn = r.steps.reduce((a, s) => a + s.input_tokens, 0), totalOut = r.steps.reduce((a, s) => a + s.output_tokens, 0);
  const reported = r.steps.some((s) => s.tokens_reported);
  $("#runtitle").textContent = `${r.kind === "analysis" ? "Analysis" : "Implementation"} · ${r.story_id} · ${r.status}`;
  $("#runmeta").textContent = [r.id, r.branch && `branch ${r.branch}`, r.target_repo && `repo ${r.target_repo}`,
    `tokens in ${fmt(totalIn)} / out ${fmt(totalOut)}${reported ? "" : " (estimated)"}`, r.error && `error: ${r.error}`].filter(Boolean).join(" · ");
  $("#steps").innerHTML = r.steps.map((s) => `<li class="${esc(s.status)}" title="${esc(s.detail || "")}"><b>${esc(s.name)}</b>${esc(s.status)}${s.kind === "agent" ? `<br><span class="muted">~${fmt(s.input_tokens)} in / ${fmt(s.output_tokens)} out</span>` : ""}</li>`).join("");
  $("#btnStop").classList.toggle("hidden", !r.active);
  $("#btnResume").classList.toggle("hidden", !["failed", "stopped", "interrupted"].includes(r.status));
  if (r.status === "awaiting_review") await renderReview(r); else $("#review").classList.add("hidden");
  if (!r.active) { loadOverview(); if (S.story?.summary.id === r.story_id) refreshStory(); }
}
$("#btnStop").onclick = async () => { try { await api(`/api/runs/${S.run}/stop`, { method: "POST" }); } catch (e) { toast(e.message); } };
$("#btnResume").onclick = async () => { try { await api(`/api/runs/${S.run}/resume`, { method: "POST" }); await refreshRun(); } catch (e) { toast(e.message); } };

function colorDiff(text) {
  return text.split("\n").map((l) => {
    const c = l.startsWith("+") && !l.startsWith("+++") ? "a" : l.startsWith("-") && !l.startsWith("---") ? "d" : /^(## |@@|diff --git)/.test(l) ? "h" : "";
    return `<span class="${c}">${esc(l)}</span>`;
  }).join("\n");
}

async function renderReview(r) {
  const el = $("#review");
  if (el.dataset.run === r.id && !el.classList.contains("hidden")) return;
  const d = await api(`/api/runs/${encodeURIComponent(r.id)}/diff`);
  const review = r.context.review || {};
  el.dataset.run = r.id;
  el.innerHTML = `<h3>Human review</h3>
    <p>Reviewer agent verdict: <b>${esc(review.verdict || "n/a")}</b> · branch <code>${esc(d.branch)}</code> in <code>${esc(d.target)}</code></p>
    ${review.text ? `<details><summary>Reviewer findings</summary><pre class="diff">${esc(review.text)}</pre></details>` : ""}
    <details open><summary>Changes against ${esc(d.base.slice(0, 10))}</summary><pre class="diff">${colorDiff(d.stat + "\n\n" + d.diff)}</pre></details>
    <div class="field"><label for="cmsg">Commit message</label><textarea id="cmsg" rows="5">${esc(d.suggested_message)}</textarea></div>
    <div class="row"><button class="btn primary" id="rvCommit">Commit all changes to ${esc(d.branch)}</button>
      <button class="btn" id="rvDone" title="Use this if you committed from your own terminal">I committed it myself</button>
      <button class="btn danger" id="rvReject">Reject</button></div>
    <p class="muted small">Nothing is pushed. After committing: push the branch and open a PR in the target repo; once merged, run <code>run_story.py record ${esc(r.story_id)}</code>.</p>`;
  el.classList.remove("hidden");
  const act = async (action) => {
    try { await api(`/api/runs/${r.id}/review`, { method: "POST", body: JSON.stringify({ action, message: $("#cmsg").value }) }); el.dataset.run = ""; await refreshRun(); toast(`Review: ${action}`); }
    catch (e) { toast(e.message); }
  };
  $("#rvCommit").onclick = () => act("commit");
  $("#rvDone").onclick = () => act("committed");
  $("#rvReject").onclick = () => { if (confirm("Reject this run? The work stays on the branch.")) act("reject"); };
}

// --- boot ------------------------------------------------------------------------------------

document.querySelectorAll(".filters .chip").forEach((b) => (b.onclick = () => {
  document.querySelectorAll(".filters .chip").forEach((x) => x.classList.toggle("on", x === b));
  S.filter = b.dataset.filter; renderTree();
}));
$("#search").addEventListener("input", renderTree);

(async function boot() {
  try {
    await loadOverview();
    const sid = store.get("story");
    if (sid && S.overview.stories.some((s) => s.id === sid)) await openStory(sid);
    else if (S.overview.next) await openStory(S.overview.next, "analysis");
    const rid = S.overview.active_run || store.get("run");
    if (rid) await openRun(rid).catch(() => {});
  } catch (e) { toast("Failed to load: " + e.message, 10000); }
  setInterval(() => { if (!S.overview?.active_run) loadOverview().catch(() => {}); }, 20000);
})();
