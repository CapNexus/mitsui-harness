"use strict";
/* Harness Studio front end. All story logic lives in the harness; this file only explains it. */

const S = { ov: null, env: null, story: null, view: null, filter: "all", run: null, runData: null, es: null, mode: "simple", threshold: 80 };
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
function cmd(text) {
  return `<div class="cmd"><code>${esc(text)}</code><button class="copy" data-copy="${esc(text)}">Copy</button></div>`;
}
document.addEventListener("click", async (ev) => {
  const b = ev.target.closest("[data-copy]");
  if (!b) return;
  try { await navigator.clipboard.writeText(b.dataset.copy); b.textContent = "Copied"; setTimeout(() => (b.textContent = "Copy"), 1500); }
  catch { toast("Copy failed. Select the text and copy it by hand."); }
});
const confClass = (c) => (c == null ? "" : c >= S.threshold ? "hi" : "lo");
const ago = (iso) => { if (!iso) return ""; const s = (Date.now() - new Date(iso).getTime()) / 1000; return s < 60 ? "just now" : s < 3600 ? `${Math.round(s / 60)} min ago` : s < 86400 ? `${Math.round(s / 3600)} h ago` : new Date(iso).toLocaleDateString(); };

// --- vocabulary -------------------------------------------------------------------------------

const STATES = {
  runnable: ["Ready to build", "Its status is ready, the agent can do it, and every story it depends on is done."],
  waiting: ["Waiting", "Ready, but another story it depends on is not done yet."],
  blocked: ["Blocked", "Needs something from Mitsui first: an approval, access, a value or a decision (see its DEP rows)."],
  human: ["Person does it", "A human task (executor: human). The harness does not run it; Studio shows the checklist."],
  done: ["Done", "Built, reviewed, merged and recorded."],
  draft: ["Draft", "Not finished being written yet."],
  next: ["Next", "The suggested next story: ready, the agent can do it, its dependencies are done, earliest due date."],
};
const stateLabel = (s) => (STATES[s] || [s])[0];
const REPO = { planning: "Planning repo (this repository)", "project-mep-AWS-Infrastructure": "Infrastructure repo (AWS baseline)", "project-mep-AWS-Code": "Code repo (the project)" };
const DEP_TYPES = { A: "a value", B: "a secret", C: "an approval", D: "access or an action by Mitsui", E: "a design decision" };
const depType = (t) => (t || "").match(/[A-E]/g)?.map((x) => DEP_TYPES[x]).join(" + ") || t;

const STEP_INFO = {
  readiness: ["Checking the facts", "Story status, dependencies and parameter values, read from the files."],
  analyze: ["Kiro reads and judges", "The read-only reviewer reads the story and project documents and scores readiness. About 30–60 seconds."],
  score: ["Working out the confidence", "60% from Kiro's judgment, 40% from the facts, capped if something blocks it."],
  classify: ["Deciding the kind of work", "Kiro picks the work type, which decides which plan template is used."],
  plan: ["Writing the plan", "Kiro writes a plan file with numbered acceptance criteria using \"shall\"."],
  plan_exists: ["Checking the plan", "The plan must exist, name the story and have numbered \"shall\" criteria."],
  write_tests: ["Writing tests first", "Kiro writes tests for each criterion before any code exists."],
  commit_tests: ["Saving the tests", "Kiro commits only the tests, so later steps can prove they were not weakened."],
  red: ["Proving the tests catch something", "The checks must fail now, because the code does not exist yet."],
  implement: ["Writing the code", "Kiro writes the code that makes the tests pass."],
  tests_unchanged: ["Checking tests were not weakened", "The committed tests must be exactly as they were."],
  green: ["Running all checks", "Format, lint, typecheck, tests (80% coverage) and synth must pass, twice."],
  validate: ["Final validation", "One more full run of every check."],
  review: ["Kiro reviews the change", "The read-only reviewer compares the real diff with the plan and the project rules."],
  commit: ["Saving the change", "Only after the reviewer says APPROVE, Kiro commits the change on the story branch."],
  human_review: ["Your review", "Look at the commits and the diff, then approve or reject. Nothing is pushed."],
};
const stepTitle = (n) => (STEP_INFO[n] || [n])[0];

function failureHint(step, detail) {
  const d = (detail || "").toLowerCase();
  if (d.includes("permission") || d.includes("denied")) return "Kiro was not allowed to write or run commands. Start Studio with the launcher (studio.cmd or ./studio.sh) so AEW_AUTO_APPROVE is on, then Resume.";
  if (d.includes("envelope")) return "Kiro's answer did not follow the expected format. This is usually a one-off: Resume to run the step again.";
  const hints = {
    readiness: "A story file could not be read. Check the story's front-matter, then run the analysis again.",
    analyze: "The analysis did not finish. Check that kiro-cli is signed in (Setup), then run the analysis again.",
    plan: "The plan file was not written where Kiro said. Resume to try again.",
    plan_exists: "The plan is missing the story ID or numbered \"shall\" criteria. Re-run from \"Writing the plan\".",
    commit_tests: "Kiro did not commit the tests. Resume to try again, or commit them yourself and re-run from \"Proving the tests catch something\".",
    red: "The checks passed before the code existed, so the new tests do not test anything new. Read the validator output, then re-run from \"Writing tests first\".",
    tests_unchanged: "The implementation changed tests that were already committed. Re-run from \"Writing the code\".",
    green: "Some checks failed. Switch the console to Detailed and read the validator output. Fix it on the branch and Resume, or re-run from \"Writing the code\".",
    validate: "The final checks failed. Read the validator output in the Detailed console, fix on the branch, then Resume.",
    review: "The review did not complete. Resume to run it again.",
    commit: d.includes("approve") ? "The reviewer asked for changes (REVISE). Read the findings in the console, then re-run from \"Writing the code\", or fix it yourself and re-run from \"Kiro reviews the change\"." : "Kiro did not commit the change. Resume, or commit it yourself and re-run from \"Kiro reviews the change\".",
  };
  return hints[step] || "Read the console for details, then Resume or re-run from an earlier step.";
}

// --- overview, setup, help ----------------------------------------------------------------------

async function loadOverview() {
  const [ov, env] = await Promise.all([api("/api/overview"), api("/api/environment")]);
  S.ov = ov; S.env = env; S.threshold = ov.threshold;
  renderTop(); renderStart(); renderFilters(); renderTree();
}

function setupChecks() {
  const e = S.env, win = e.os === "windows";
  const checks = [
    { ok: !!e.kiro_cli, title: "Kiro CLI is installed", why: "Kiro is the agent that analyzes and builds stories.",
      fix: ["Install Kiro CLI from kiro.dev, then open a new terminal and sign in:", "kiro-cli login"] },
    { ok: e.auto_approve, title: "Kiro may write files and run commands (AEW_AUTO_APPROVE)", why: "Needed to implement. Analysis works without it.",
      fix: ["Stop Studio (Ctrl+C) and start it with the launcher from the repository root:", win ? ".\\studio" : "./studio.sh"] },
    { ok: !!e.npm, title: "Node.js and npm are installed", why: "The code repositories need npm for tests and cdk synth.",
      fix: ["Install Node.js LTS, then open a new terminal and restart Studio:", win ? "winget install OpenJS.NodeJS.LTS" : "brew install node"] },
  ];
  for (const [m, ok] of Object.entries(e.submodules || {})) {
    checks.push({ ok, title: `${m} is checked out`, why: "Stories that change this repository run inside it.", fix: ["From the repository root:", "git submodule update --init"] });
  }
  checks.push({ ok: !e.parent_dirty.length, soft: true, title: "This repository has no uncommitted changes",
    why: "Stories in the planning repo need a clean working tree so their commits hold only their own work.",
    fix: [`Uncommitted: ${e.parent_dirty.slice(0, 6).join(", ")}${e.parent_dirty.length > 6 ? " …" : ""}. Commit or stash them:`, "git status"] });
  return checks;
}

function renderTop() {
  const t = S.ov.tokens, a = t.analysis.input + t.analysis.output, i = t.implementation.input + t.implementation.output;
  $("#tokens").textContent = `Kiro usage ≈ ${fmt(a + i)} tokens${t.any_reported ? "" : " (estimated)"}`;
  const bad = setupChecks().filter((c) => !c.ok && !c.soft).length;
  const b = $("#btnSetup");
  b.textContent = bad ? `Setup: ${bad} to fix` : "Setup: ready";
  b.className = `pill pill-btn ${bad ? "bad" : "ok"}`;
}

function openSetup() {
  $("#setupBody").innerHTML = `<p class="panel-intro">Studio checks these every time it loads. Fix anything marked ✗, then reload the page.</p>
    <ul class="checklist">${setupChecks().map((c) => `<li class="${c.ok ? "ok" : c.soft ? "info" : "bad"}"><span class="ic">${c.ok ? "✓" : c.soft ? "!" : "✗"}</span>
      <div><b>${esc(c.title)}</b><span class="fix">${esc(c.why)}</span>${c.ok ? "" : `<span class="fix">${esc(c.fix[0])}</span>${cmd(c.fix[1])}`}</div></li>`).join("")}</ul>
    <p class="muted small">Validator shell: <code>${esc(S.env.bash)}</code> · Studio database: <code>${esc(S.env.db)}</code></p>`;
  $("#setupDlg").showModal();
}

function openHelp() {
  $("#helpBody").innerHTML = `
    <p>Studio helps you take one user story from idea to a reviewed branch. Kiro, the AI agent, does the reading, planning, testing and coding. You make the decisions. Everything Studio does is the same as the harness command line (<code>harness/run_story.py</code>).</p>
    <h3>The five stages of a story</h3>
    <ol>
      <li><b>Understand</b>: read what the story asks, what it depends on and which repository it changes.</li>
      <li><b>Analyze</b>: Kiro (read-only) reads the story and the project documents and gives a <b>confidence score</b>. ${S.threshold}% or more is a good start.</li>
      <li><b>Implement</b>: Kiro plans, writes tests first, writes the code, runs every check, reviews its own change and commits it on a new <b>story branch</b>. You can watch each step live, stop it and resume it.</li>
      <li><b>Review</b>: you look at the commits and the diff and approve or reject. Nothing is pushed for you.</li>
      <li><b>Ship</b>: you push the branch, open a pull request, and after it is merged record the story as done.</li>
    </ol>
    <h3>Words you will see</h3>
    <dl class="gloss">
      <dt>Ready to build</dt><dd>Status ready, the agent can do it, and every story it depends on is done.</dd>
      <dt>Waiting</dt><dd>Ready, but a story it depends on is not done yet.</dd>
      <dt>Blocked</dt><dd>Needs something from Mitsui first (a DEP row).</dd>
      <dt>DEP rows</dt><dd>Things Mitsui provides, in <code>user-stories/dependencies/README.md</code>. Type A is a value, B a secret, C an approval, D access or an action, E a design decision. A and B can be built against placeholders; C, D and E block the story.</dd>
      <dt>Confidence</dt><dd>60% Kiro's judgment plus 40% facts from the files. An unfinished story dependency caps it at 40%; an open C, D or E dependency at 60%.</dd>
      <dt>Story branch</dt><dd>A new git branch (for example <code>story/F02-S02-…</code>) in the repository the story changes. All of Kiro's work goes there.</dd>
      <dt>Scaffold unlock</dt><dd>Lets the first story in an empty repository add toolchain files (TypeScript, Jest, ESLint, Prettier). Only for F02-S02 and F02-S12.</dd>
      <dt>Red / green</dt><dd>Red: the checks must fail before the code exists, so the tests really test something. Green: they must pass after.</dd>
      <dt>Validator</dt><dd><code>scripts/validate.sh</code>: format, lint, typecheck, tests with 80% coverage, cdk synth and the freeze dates.</dd>
      <dt>Reviewer verdict</dt><dd>Kiro's read-only reviewer answers APPROVE or REVISE. Kiro only commits the change after APPROVE.</dd>
      <dt>Resume / Re-run from</dt><dd>Resume continues from the step that did not finish. Re-run from runs a chosen step and every step after it again.</dd>
      <dt>Tokens</dt><dd>An estimate of how much text Kiro read and wrote. Kiro bills credits to your account and does not report exact numbers.</dd>
    </dl>
    <h3>Safety</h3>
    <ul>
      <li>Kiro cannot deploy, change AWS, or edit the harness's own rules. Hooks block it.</li>
      <li>Kiro only works on the story branch. You decide what is pushed and merged.</li>
      <li>Every run is saved, so you can close the browser or restart Studio and resume later.</li>
    </ul>
    <p class="muted small">More: <code>README.md</code>, <code>HARNESS.md</code> and <code>harness/studio/README.md</code> in the repository.</p>`;
  $("#helpDlg").showModal();
}
document.querySelectorAll("dialog [data-close]").forEach((b) => (b.onclick = () => b.closest("dialog").close()));
$("#btnSetup").onclick = openSetup;
$("#btnHelp").onclick = openHelp;
$("#btnLegend").onclick = () => {
  const l = $("#legend"), hidden = l.classList.toggle("hidden");
  $("#btnLegend").setAttribute("aria-expanded", String(!hidden));
  l.innerHTML = ["next", "runnable", "waiting", "blocked", "human", "done"].map((k) => `<span class="state ${k}">${stateLabel(k)}</span><span>${esc(STATES[k][1])}</span>`).join("")
    + `<span class="conf hi">85%</span><span>Latest confidence score. Green is ${S.threshold}% or more.</span>`;
};

// --- sidebar --------------------------------------------------------------------------------------

function renderStart() {
  const ov = S.ov, el = $("#startHere"), s = ov.stories.find((x) => x.id === ov.next);
  const active = ov.active_run ? `<div class="callout small">A run is in progress: <a href="#" id="openActive">${esc(ov.active_run)}</a></div>` : "";
  if (!s) { el.innerHTML = `<div class="eyebrow">Start here</div><p>${esc(ov.next_reason)}</p>${active}`; }
  else {
    el.innerHTML = `<div class="eyebrow">Start here · suggested next story</div>
      <div class="title"><span class="sid">${esc(s.id)}</span> ${esc(s.title)}</div>
      <p>${esc(REPO[s.repo] || s.repo)} · due ${esc(s.due)}${s.confidence != null ? ` · confidence <span class="conf ${confClass(s.confidence)}">${s.confidence}%</span>` : ""}</p>
      <button class="btn primary" id="openNext">Work on this story →</button>${active}`;
    $("#openNext").onclick = () => openStory(s.id);
  }
  const oa = $("#openActive"); if (oa) oa.onclick = (e) => { e.preventDefault(); openRun(ov.active_run); };
}

const FILTERS = [["all", "All"], ["runnable", "Ready"], ["waiting", "Waiting"], ["blocked", "Blocked"], ["done", "Done"]];
function inFilter(s, f) { return f === "all" || (f === "blocked" ? ["blocked", "human", "draft"].includes(s.state) : s.state === f); }
function renderFilters() {
  $("#filters").innerHTML = FILTERS.map(([k, l]) => `<button class="chip ${S.filter === k ? "on" : ""}" data-f="${k}" title="${esc(k === "all" ? "Every story" : (STATES[k] || ["", ""])[1])}">${l}<span class="n">${S.ov.stories.filter((s) => inFilter(s, k)).length}</span></button>`).join("");
  $("#filters").querySelectorAll(".chip").forEach((b) => (b.onclick = () => { S.filter = b.dataset.f; renderFilters(); renderTree(); }));
}

function renderTree() {
  const ov = S.ov, q = $("#search").value.trim().toLowerCase(), open = new Set(JSON.parse(store.get("openFeatures") || "[]"));
  const match = (s) => inFilter(s, S.filter) && (!q || s.id.toLowerCase().includes(q) || s.title.toLowerCase().includes(q));
  $("#tree").innerHTML = ov.features.map((f) => {
    const all = ov.stories.filter((s) => s.feature_folder === f.folder), rows = all.filter(match);
    if (!rows.length) return "";
    const done = all.filter((s) => s.state === "done").length;
    const isOpen = q || S.filter !== "all" || open.has(f.folder) || rows.some((r) => r.id === ov.next || r.id === S.story?.summary.id);
    return `<details data-f="${esc(f.folder)}" ${isOpen ? "open" : ""}>
      <summary><span class="sid">${esc(f.id)}</span><span class="ft">${esc(f.title)}</span><span class="count">${done}/${all.length} done</span></summary>
      <div class="progress" aria-hidden="true"><i style="width:${all.length ? (100 * done) / all.length : 0}%"></i></div>
      ${rows.map((s) => { const st = s.id === ov.next ? "next" : s.state; return `<button class="srow ${S.story?.summary.id === s.id ? "sel" : ""}" data-id="${esc(s.id)}" title="${esc(s.title)} · ${esc(STATES[st]?.[1] || "")}">
        <span class="sid">${esc(s.id)}</span><span class="t">${esc(s.title)}</span>
        <span>${s.confidence != null && s.state !== "human" ? `<span class="conf ${confClass(s.confidence)}" title="Latest confidence">${s.confidence}%</span> ` : ""}<span class="state ${esc(st)}">${esc(stateLabel(st))}</span></span></button>`; }).join("")}
    </details>`;
  }).join("") || `<p class="muted small">No stories match. Clear the search or pick another filter.</p>`;
  $("#tree").querySelectorAll(".srow").forEach((r) => (r.onclick = () => openStory(r.dataset.id)));
  $("#tree").querySelectorAll("details").forEach((d) => d.addEventListener("toggle", () => {
    store.set("openFeatures", JSON.stringify([...$("#tree").querySelectorAll("details[open]")].map((x) => x.dataset.f)));
  }));
}
$("#search").addEventListener("input", renderTree);

// --- story workspace ----------------------------------------------------------------------------

const latest = (kind) => S.story?.runs.find((r) => r.kind === kind);

function journey() {
  const st = S.story, s = st.summary, a = latest("analysis"), i = latest("implementation");
  const conf = a?.status === "completed" ? a.confidence : null;
  const stuck = ["blocked", "waiting", "human", "draft"].includes(s.state);
  let cur;
  if (s.state === "done") cur = "ship";
  else if (i && ["queued", "running", "failed", "stopped", "interrupted"].includes(i.status)) cur = "implement";
  else if (i?.status === "awaiting_review") cur = "review";
  else if (i?.status === "completed") cur = "ship";
  else if (stuck) cur = "understand";
  else if (conf == null) cur = "analyze";
  else cur = "implement";
  const order = ["understand", "analyze", "implement", "review", "ship"];
  const ci = order.indexOf(cur);
  const status = (k, idx) => (s.state === "done" ? "done" : idx < ci ? "done" : idx === ci ? (stuck && k === "understand" ? "blocked" : "current") : "todo");
  const sub = {
    understand: stuck ? stateLabel(s.state) : "read the story",
    analyze: conf != null ? `${conf}% confidence` : a && ["queued", "running"].includes(a.status) ? "running…" : "not yet",
    implement: i ? i.status.replace("_", " ") : "not started",
    review: i?.status === "awaiting_review" ? "your turn" : i?.status === "completed" ? "approved" : "after implement",
    ship: s.state === "done" ? "recorded" : i?.status === "completed" ? "push & PR" : "after review",
  };
  return { cur, steps: order.map((k, idx) => ({ k, status: status(k, idx), sub: sub[k] })), conf, a, i };
}

function nextAction(j) {
  const st = S.story, s = st.summary;
  if (s.state === "waiting") return { tone: "warn", t: "This story is waiting for other stories", d: `Finish ${s.waiting_on.join(", ")} first. You can still read it and run the analysis.`, acts: [[`Open ${s.waiting_on[0]}`, () => openStory(s.waiting_on[0])], ["Analyze anyway", () => go("analyze"), "analyze"]] };
  if (s.state === "blocked") {
    const open = st.dependencies.filter((d) => d.status !== "resolved").map((d) => `${d.id} (${depType(d.type)}${d.owner ? `, ${d.owner}` : ""})`);
    return { tone: "bad", t: "Blocked: waiting on Mitsui", d: `Needs ${open.join("; ") || "an open dependency"}. When it is resolved, update the dependency register and set the story to ready.`, acts: [["See what it needs", () => go("understand"), "understand"]] };
  }
  if (s.state === "human") return { tone: "info", t: "A person does this story", d: "The harness does not run human stories. Use the acceptance criteria and gates below as your checklist.", acts: [] };
  if (j.cur === "ship") return s.state === "done" ? { tone: "ok", t: "Done", d: "This story is merged and recorded.", acts: [] }
    : { tone: "ok", t: "Approved. Push the branch and open a pull request", d: "Then, after the pull request is merged, record the story as done.", acts: [["Show the commands", () => go("ship"), "ship"]] };
  if (j.cur === "review") return { tone: "info", t: "Your turn: review Kiro's change", d: `Kiro committed the change on ${j.i.branch}. Look at the commits and the diff, then approve or reject.`, acts: [["Review now", () => go("review"), "review"]] };
  if (j.cur === "implement" && j.i && ["queued", "running"].includes(j.i.status)) return { tone: "info", t: "Kiro is building this story", d: "Watch each step in Live progress. You can stop at any time and resume later.", acts: [["Watch progress", () => openRun(j.i.id)]] };
  if (j.cur === "implement" && j.i && ["failed", "stopped", "interrupted"].includes(j.i.status)) {
    const failed = j.i.status === "failed";
    return { tone: failed ? "bad" : "warn", t: failed ? "The build stopped on a problem" : `The build is ${j.i.status}`, d: failed ? "Open it to see which step failed and what to do." : "Resume it to continue from where it stopped.", acts: [["Open the build", () => openRun(j.i.id)]] };
  }
  if (j.cur === "analyze") {
    if (j.a && ["queued", "running"].includes(j.a.status)) return { tone: "info", t: "Analysis is running", d: "Kiro is reading the story and the project documents. This takes about a minute.", acts: [["Watch progress", () => openRun(j.a.id)]] };
    return { tone: "info", t: "Next: check whether Kiro can build this story", d: "Run the analysis. Kiro reads the story and project documents (read-only) and gives a confidence score.", acts: [["Run analysis", startAnalysis]] };
  }
  if (j.conf != null && j.conf < S.threshold) return { tone: "warn", t: `Confidence ${j.conf}% is below ${S.threshold}%`, d: "Look at the risks and questions first. Improve the story and re-run the analysis, or continue with a reason.", acts: [["See what to fix", () => go("analyze"), "analyze"], ["Continue anyway", () => go("implement"), "implement"]] };
  return { tone: "ok", t: `Ready to build (confidence ${j.conf}%)`, d: "Check the branch name and start. Kiro will plan, test, code, check and commit on a new branch.", acts: [["Set up the build", () => go("implement"), "implement"]] };
}

const STAGES = [["understand", "Understand"], ["analyze", "Analyze"], ["implement", "Implement"], ["review", "Review"], ["ship", "Ship"]];
function go(view) { S.view = view; renderStory(); $("#workspace").scrollIntoView({ behavior: "smooth", block: "start" }); }

async function openStory(id, view) {
  S.story = await api(`/api/stories/${encodeURIComponent(id)}`);
  S.view = view || null;
  store.set("story", id);
  renderTree(); renderStory();
  const live = S.story.runs.find((r) => ["queued", "running", "awaiting_review"].includes(r.status));
  if (live && S.run !== live.id) openRun(live.id);
}
async function refreshStory() { if (S.story) { S.story = await api(`/api/stories/${encodeURIComponent(S.story.summary.id)}`); renderStory(); } }

function renderStory() {
  const st = S.story, s = st.summary, j = journey(), view = S.view || j.cur, na = nextAction(j);
  na.acts = na.acts.filter((a) => a[2] !== view);
  const label = st.is_next ? "next" : s.state;
  $("#workspace").innerHTML = `
    <div class="ws-head"><div><span class="sid">${esc(s.id)} · feature ${esc(s.feature)}</span><h1>${esc(s.title)}</h1></div>
      <span class="state ${esc(label)}" title="${esc((STATES[label] || ["", ""])[1])}">${esc(stateLabel(label))}</span></div>
    <div class="facts">
      <span title="The repository this story changes">Changes: <b>${esc(REPO[s.repo] || s.repo)}</b></span>
      <span title="Who is accountable">Owner: <b>${esc(s.owner || "—")}</b></span>
      <span>Due: <b>${esc(s.due || "—")}</b></span>
      <span title="agent: Kiro does it · mixed: Kiro plus a person · human: a person">Done by: <b>${esc({ agent: "Kiro", mixed: "Kiro + a person", human: "a person" }[s.executor] || s.executor)}</b></span>
      <span title="build: no Mitsui dependency · integrate: needs Mitsui's environment or approval">Kind: <b>${esc({ build: "build (sandbox)", integrate: "integrate (needs Mitsui)" }[s.tier] || s.tier)}</b></span>
    </div>
    <nav class="journey" aria-label="Story stages">${j.steps.map((x, idx) => `<button class="jstep ${x.status} ${view === x.k ? "viewing" : ""}" data-v="${x.k}" ${x.k === j.cur ? 'aria-current="step"' : ""}>
      <span class="dot">${x.status === "done" ? "✓" : x.status === "blocked" ? "!" : idx + 1}</span><span class="jl">${STAGES[idx][1]}</span><span class="js">${esc(x.sub)}</span></button>`).join("")}</nav>
    <div class="banner ${na.tone}" role="status"><div><div class="bt">${esc(na.t)}</div><div class="bd">${esc(na.d)}</div></div>
      <div class="acts">${na.acts.map((a, k) => `<button class="btn ${k === 0 ? "primary" : ""}" data-act="${k}">${esc(a[0])}</button>`).join("")}</div></div>
    <div id="viewbody"></div>
    <p class="muted small" style="margin-top:18px">Story file: <code>${esc(s.path)}</code> · <a href="#" id="showHistory">Run history (${st.runs.length})</a></p>`;
  $("#workspace").querySelectorAll(".jstep").forEach((b) => (b.onclick = () => { S.view = b.dataset.v; renderStory(); }));
  $("#workspace").querySelectorAll("[data-act]").forEach((b) => (b.onclick = na.acts[+b.dataset.act][1]));
  $("#showHistory").onclick = (e) => { e.preventDefault(); S.view = "history"; renderStory(); };
  ({ understand: viewUnderstand, analyze: viewAnalyze, implement: viewImplement, review: viewReview, ship: viewShip, history: viewHistory })[view]();
}

function viewUnderstand() {
  const st = S.story, s = st.summary, r = st.readiness;
  const deps = st.dependencies.length ? `<h4>Needs from Mitsui (DEP rows)</h4><ul class="checklist">${st.dependencies.map((d) => {
      const hard = /[CDE]/.test(d.type || ""), ok = d.status === "resolved";
      return `<li class="${ok ? "ok" : hard ? "bad" : "info"}"><span class="ic">${ok ? "✓" : hard ? "✗" : "!"}</span>
      <div><b>${esc(d.id)}</b> ${esc(d.what || "")}<span class="fix">${esc(depType(d.type))} · ${esc(d.status)}${d.owner ? ` · owner ${esc(d.owner)}` : ""}${!ok && !hard ? " · Kiro builds against a placeholder until it arrives" : ""}</span></div></li>`; }).join("")}</ul>` : "";
  const waits = s.depends_on.length ? `<h4>Stories that must be done first</h4><ul class="checklist">${s.depends_on.map((d) => `<li class="${s.waiting_on.includes(d) ? "bad" : "ok"}"><span class="ic">${s.waiting_on.includes(d) ? "✗" : "✓"}</span><div><a href="#" data-story="${esc(d)}">${esc(d)}</a> ${s.waiting_on.includes(d) ? "is not done yet" : "is done"}</div></li>`).join("")}</ul>` : "";
  const gates = s.human_gates.length ? `<h4>Where a person must act</h4><ul>${s.human_gates.map((g) => `<li>${esc(g)}</li>`).join("")}</ul>` : "";
  $("#viewbody").innerHTML = `<p class="panel-intro">What the story asks, what it depends on, and the facts the harness checked. The story file is the source of truth.</p>
    ${waits}${deps}${gates}
    <details class="box"><summary>Readiness facts (${r.score}%${r.cap < 100 ? `, capped at ${r.cap}%` : ""})</summary>${factorList(r.factors)}</details>
    <details class="box" open><summary>The story</summary><div class="md">${md(st.text)}</div></details>`;
  $("#viewbody").querySelectorAll("[data-story]").forEach((x) => (x.onclick = (e) => { e.preventDefault(); openStory(x.dataset.story); }));
}

function factorList(factors) {
  return `<ul class="checklist">${factors.map((f) => `<li class="${f.level === "ok" ? "ok" : f.level === "block" ? "bad" : "info"}"><span class="ic">${f.level === "ok" ? "✓" : f.level === "block" ? "✗" : "!"}</span><div><b>${esc(f.name)}</b><span class="fix">${esc(f.detail)}</span></div></li>`).join("")}</ul>`;
}

async function startAnalysis() {
  try { const { run_id } = await api(`/api/stories/${S.story.summary.id}/analyze`, { method: "POST" }); await refreshStory(); openRun(run_id); }
  catch (e) { toast(e.message); }
}

function viewAnalyze() {
  const a = latest("analysis"), r = a?.result, running = a && ["queued", "running"].includes(a.status);
  let html = `<p class="panel-intro">Kiro's read-only reviewer reads the story, its feature, the dependency register, the parameters, the ADRs, the knowledge documents and the project rules, then judges whether it can build the story now. Nothing is changed. Same as <code>run_story.py analyze</code>.</p>
    <div class="row"><button class="btn ${r ? "" : "primary"}" id="btnAnalyze" ${running || S.ov.active_run ? "disabled" : ""}>${running ? "Analysis running…" : r ? "Run the analysis again" : "Run analysis"}</button>
    ${S.ov.active_run && !running ? `<span class="muted small">Another run is active; wait for it to finish.</span>` : ""}
    ${a ? `<span class="muted small">Last run ${esc(ago(a.updated_at))} · <a href="#" data-run="${esc(a.id)}">open its log</a></span>` : ""}</div>`;
  if (a?.status === "failed") html += `<div class="callout bad"><b>The analysis failed.</b> ${esc(failureHint("analyze", a.error))}<br><span class="small">${esc(a.error)}</span></div>`;
  if (r) {
    const c = r.confidence, color = c >= S.threshold ? "var(--ok)" : c >= 60 ? "var(--warn)" : "var(--bad)";
    const why = r.cap === 40 ? "a story it depends on is not done" : r.cap === 60 ? "an approval, access or decision from Mitsui is still open" : "of the story's status";
    const verdict = c >= S.threshold ? `<div class="callout ok"><b>Good to start.</b> ${c}% is at least ${S.threshold}%.</div>`
      : `<div class="callout warn"><b>${c}% is below ${S.threshold}%.</b> ${r.capped ? `It is capped at ${r.cap}% because ${why}. ` : ""}Answer the questions below in the story or its sources and run the analysis again, or continue with a reason.</div>`;
    html += `<div class="section gauge"><div class="dial" style="background:conic-gradient(${color} ${c * 3.6}deg, var(--chip) 0)" role="img" aria-label="Confidence ${c}%"><span>${c}%</span></div>
      <div class="bars">${Object.entries(r.dimensions || {}).map(([k, v]) => `<span>${esc(k.replace(/_/g, " "))}</span><span class="bar"><i style="width:${Number(v)}%"></i></span><span>${Number(v)}</span>`).join("")}</div></div>
      <p class="small muted">${c}% = 60% × Kiro's ${r.agent} + 40% × facts ${r.readiness}${r.capped ? `, capped at ${r.cap}` : ""}.</p>
      ${verdict}<p>${esc(r.summary || "")}</p>
      ${r.questions?.length ? `<h4>Questions to answer</h4><ol>${r.questions.map((x) => `<li>${esc(x)}</li>`).join("")}</ol>` : ""}
      ${r.risks?.length ? `<details class="box"><summary>Risks Kiro sees (${r.risks.length})</summary><ul>${r.risks.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></details>` : ""}
      ${r.relevant_docs?.length ? `<details class="box"><summary>Documents that matter for this story (${r.relevant_docs.length})</summary><ul>${r.relevant_docs.map((x) => `<li><code>${esc(x)}</code></li>`).join("")}</ul></details>` : ""}
      <div class="row"><button class="btn ${c >= S.threshold ? "primary" : ""}" id="goImpl">Continue to Implement →</button></div>`;
  }
  $("#viewbody").innerHTML = html;
  $("#btnAnalyze").onclick = startAnalysis;
  $("#viewbody").querySelectorAll("[data-run]").forEach((x) => (x.onclick = (e) => { e.preventDefault(); openRun(x.dataset.run); }));
  const gi = $("#goImpl"); if (gi) gi.onclick = () => go("implement");
}

function viewImplement() {
  const st = S.story, s = st.summary, a = latest("analysis"), i = latest("implementation");
  const conf = a?.status === "completed" ? a.confidence : null;
  if (i && !["completed", "rejected"].includes(i.status)) {
    $("#viewbody").innerHTML = `<div class="callout"><b>This story already has a build:</b> ${esc(i.status.replace("_", " "))} on <code>${esc(i.branch)}</code>. Its progress is in Live progress below.</div>
      <div class="row"><button class="btn primary" id="openLive">Show its progress</button></div>`;
    $("#openLive").onclick = () => openRun(i.id);
    return;
  }
  const scaffoldDefault = ["F02-S02", "F02-S12"].includes(s.id);
  $("#viewbody").innerHTML = `
    <p class="panel-intro">Kiro runs the harness <code>plan_build</code> workflow on a new branch: decide the work type → plan → tests first → prove they fail → code → prove tests unchanged → all checks pass → self-review → commit. It never deploys and never pushes. You review at the end.</p>
    <div class="field"><label for="branch">Branch for this story</label>
      <span class="hint">Created in the ${esc(REPO[s.repo] || s.repo)} from its current branch. All of Kiro's commits go here. Suggested from the story ID; you can change it.</span>
      <input type="text" id="branch" value="${esc(st.branch_suggestion)}" spellcheck="false"></div>
    <label class="checkline"><input type="checkbox" id="scaffold" ${scaffoldDefault ? "checked" : ""}>
      <span><b>Scaffold unlock</b> — first story in an empty repository only.<br><span class="muted small">Lets Kiro add toolchain files (tsconfig, Jest, ESLint, Prettier) that are otherwise protected. ${scaffoldDefault ? "Recommended for this story." : "Leave this off: it is for F02-S02 and F02-S12."}</span></span></label>
    <div class="field ${conf != null && conf < S.threshold ? "" : "hidden"}"><label for="override">Why start below ${S.threshold}%?</label>
      <span class="hint">Saved with the run, so the team can see why it went ahead.</span><textarea id="override" rows="2"></textarea></div>
    <h4>Before you start</h4><ul class="checklist" id="pre"><li class="info"><span class="ic">…</span><div>Checking…</div></li></ul>
    <div class="row"><button class="btn primary" id="btnStart" disabled>Start building</button><span class="muted small" id="startHint"></span></div>`;
  let timer;
  const body = () => ({ branch: $("#branch").value.trim(), scaffold: $("#scaffold").checked, override_reason: $("#override").value });
  const check = async () => {
    const r = await api(`/api/stories/${s.id}/preflight`, { method: "POST", body: JSON.stringify(body()) }).catch((e) => ({ ok: false, errors: [e.message] }));
    const confOk = conf != null && (conf >= S.threshold || $("#override").value.trim());
    const first = conf == null
      ? `<li class="bad"><span class="ic">✗</span><div><b>Analysis not done</b><span class="fix">Run the analysis first (Analyze).</span></div></li>`
      : `<li class="${confOk ? "ok" : "info"}"><span class="ic">${confOk ? "✓" : "!"}</span><div><b>Confidence ${conf}%</b><span class="fix">${conf >= S.threshold ? "Good to start." : confOk ? "Below the threshold; your reason is recorded." : `Below ${S.threshold}%: write a reason above to continue.`}</span></div></li>`;
    const errs = r.errors.filter((e) => !/analysis|confidence/i.test(e));
    $("#pre").innerHTML = first + (errs.length ? errs.map((e) => `<li class="bad"><span class="ic">✗</span><div>${esc(friendlyPreflight(e))}</div></li>`).join("")
      : `<li class="ok"><span class="ic">✓</span><div><b>Repository, branch and tools are ready</b><span class="fix">Kiro is installed and allowed to work, the repository is clean, and the branch name is new.</span></div></li>`);
    $("#btnStart").disabled = !r.ok;
    $("#startHint").textContent = r.ok ? "Kiro starts immediately. You can stop at any time." : "Fix the items marked ✗ first.";
  };
  const later = () => { clearTimeout(timer); timer = setTimeout(check, 350); };
  ["#branch", "#override"].forEach((q) => $(q).addEventListener("input", later));
  $("#scaffold").addEventListener("change", later);
  $("#btnStart").onclick = async () => {
    $("#btnStart").disabled = true;
    try { const { run_id } = await api(`/api/stories/${s.id}/implement`, { method: "POST", body: JSON.stringify(body()) }); await refreshStory(); openRun(run_id); }
    catch (e) { toast(friendlyPreflight(e.message), 9000); check(); }
  };
  check();
}

function friendlyPreflight(e) {
  if (/AEW_AUTO_APPROVE/.test(e)) return "Kiro is not allowed to write files yet. Restart Studio with the launcher (studio.cmd or ./studio.sh).";
  if (/uncommitted changes/.test(e)) return `The repository has uncommitted changes. Commit or stash them first, so the story's commits contain only its own work. (${e.split(":").slice(-1)[0].trim().slice(0, 160)})`;
  if (/already exists/.test(e)) return "A branch with this name already exists. Change the name, or delete the old branch if it is not needed.";
  if (/already on/.test(e)) return "The repository is already on this branch. Switch it back to its base branch (for example main) first.";
  if (/not a valid branch/.test(e)) return "That branch name is not valid. Use letters, numbers, dashes and slashes, for example story/F02-S02-cdk-app.";
  if (/npm/.test(e)) return "npm is not installed or not on PATH. Install Node.js LTS (see Setup), open a new terminal and restart Studio.";
  if (/kiro-cli/.test(e)) return "kiro-cli is not on PATH. Install it and sign in (see Setup).";
  if (/not checked out/.test(e)) return "The repository for this story is not checked out. Run: git submodule update --init";
  if (/executor: human/.test(e)) return "A person does this story; the harness does not run it.";
  return e;
}

async function viewReview() {
  const i = latest("implementation");
  if (!i || !["awaiting_review", "completed", "rejected"].includes(i.status)) {
    $("#viewbody").innerHTML = `<p class="panel-intro">When Kiro has finished and committed the change, you review it here before anything is pushed.</p><div class="callout">Nothing to review yet.</div>`;
    return;
  }
  $("#viewbody").innerHTML = `<p class="muted">Loading the change…</p>`;
  const d = await api(`/api/runs/${encodeURIComponent(i.id)}/diff`);
  const lines = (d.review || "").trim().split("\n"), verdict = lines[lines.length - 1] || "n/a";
  const decided = i.status !== "awaiting_review", repoName = REPO[S.story.summary.repo] || d.target;
  $("#viewbody").innerHTML = `
    <p class="panel-intro">Kiro's work is committed on <code>${esc(d.branch)}</code> in the ${esc(repoName)}. Nothing is pushed. Read it the way you would read a colleague's pull request.</p>
    ${decided ? `<div class="callout ${i.status === "completed" ? "ok" : "bad"}">You ${i.status === "completed" ? "approved" : "rejected"} this change.</div>` : ""}
    <h4>Kiro's reviewer said: <span class="state ${verdict === "APPROVE" ? "done" : "blocked"}">${esc(verdict)}</span></h4>
    ${d.review ? `<details class="box"><summary>Reviewer findings</summary><pre class="diff">${esc(d.review)}</pre></details>` : ""}
    <h4>Commits on the branch (${d.commits.length})</h4><pre class="diff">${esc(d.commits.join("\n") || "(none)")}</pre>
    ${d.uncommitted.length ? `<div class="callout warn"><b>Left uncommitted by Kiro:</b> ${d.uncommitted.map(esc).join(", ")}. Commit or discard them before you push.</div>` : ""}
    <h4>Check before you approve</h4>
    <ul class="checklist">
      <li class="info"><span class="ic">?</span><div>Every acceptance criterion in the story has code and a test${d.plan ? ` (plan: <code>${esc(d.plan)}</code>)` : ""}.</div></li>
      <li class="info"><span class="ic">?</span><div>Only files in the ${esc(repoName)} changed, and nothing unrelated.</div></li>
      <li class="info"><span class="ic">?</span><div>No deploy commands, no AWS changes, no secrets, no hard-coded Mitsui values.</div></li>
      <li class="info"><span class="ic">?</span><div>Tests were not weakened or skipped to make things pass.</div></li>
    </ul>
    <details class="box" open><summary>The full change against ${esc(d.base.slice(0, 10))}</summary><pre class="diff">${colorDiff(d.stat + "\n\n" + d.diff)}</pre></details>
    ${decided ? "" : `<div class="field"><label for="rvNote">Note (optional)</label><span class="hint">Saved with your decision.</span><textarea id="rvNote" rows="2"></textarea></div>
    <div class="row"><button class="btn primary" id="rvApprove">Approve: ready to push</button><button class="btn danger" id="rvReject">Reject</button>
      <span class="muted small">Want a change first? Edit and commit on the branch yourself, or use "Re-run from" in Live progress.</span></div>`}`;
  if (decided) return;
  const act = async (action) => {
    try {
      await api(`/api/runs/${i.id}/review`, { method: "POST", body: JSON.stringify({ action, note: $("#rvNote").value }) });
      toast(action === "approve" ? "Approved. Next: push and open a pull request." : "Rejected. The commits stay on the branch.");
      await refreshStory(); refreshRun(); if (action === "approve") go("ship");
    } catch (e) { toast(e.message); }
  };
  $("#rvApprove").onclick = () => act("approve");
  $("#rvReject").onclick = () => { if (confirm("Reject this change? The commits stay on the branch; nothing is deleted.")) act("reject"); };
}

async function viewShip() {
  const s = S.story.summary, i = latest("implementation");
  if (s.state === "done") { $("#viewbody").innerHTML = `<div class="callout ok"><b>Done.</b> This story is merged and recorded.</div>`; return; }
  if (!i || i.status !== "completed") { $("#viewbody").innerHTML = `<p class="panel-intro">After you approve Kiro's change, this page shows how to push it, open a pull request and record the story.</p><div class="callout">Nothing to ship yet.</div>`; return; }
  const d = await api(`/api/runs/${encodeURIComponent(i.id)}/diff`);
  $("#viewbody").innerHTML = `
    <p class="panel-intro">Studio never pushes for you. Run these from the repository root.</p>
    <h4>1. Push the branch</h4>${cmd(d.push_cmd)}
    <h4>2. Open a pull request</h4>
    ${d.compare_url ? `<p><a href="${esc(d.compare_url)}" target="_blank" rel="noopener">Open a pull request for ${esc(d.branch)} ↗</a></p>` : `<p>Open a pull request for <code>${esc(d.branch)}</code> on the repository's web page.</p>`}
    <p class="muted small">A teammate reviews and merges it.${s.repo === "planning" ? " Planning changes go into <code>main</code>, which only accepts pull requests." : ""}</p>
    ${d.record_cmd ? `<h4>3. After it is merged: record the story as done</h4><p class="muted small">This commits the new submodule version and <code>status: done</code> together in this repository.</p>${cmd(d.record_cmd)}`
      : `<h4>3. After it is merged</h4><p>Set <code>status: done</code> in the story file, in the same pull request or a follow-up.</p>`}`;
}

function viewHistory() {
  const runs = S.story.runs;
  $("#viewbody").innerHTML = runs.length ? `<p class="panel-intro">Every analysis and build of this story, newest first. Open one to see its steps and console.</p>
    <div class="tblwrap"><table class="tbl"><thead><tr><th>When</th><th>What</th><th>Result</th><th>Branch</th><th>Confidence</th><th></th></tr></thead><tbody>
    ${runs.map((r) => `<tr><td>${esc(ago(r.created_at))}</td><td>${r.kind === "analysis" ? "Analysis" : "Build"}</td><td>${esc(r.status.replace("_", " "))}</td><td>${r.branch ? `<code>${esc(r.branch)}</code>` : ""}</td><td>${r.confidence ?? ""}</td><td><a href="#" data-run="${esc(r.id)}">open</a></td></tr>`).join("")}
    </tbody></table></div>` : `<p class="muted">No runs yet. Start with Analyze.</p>`;
  $("#viewbody").querySelectorAll("[data-run]").forEach((x) => (x.onclick = (e) => { e.preventDefault(); openRun(x.dataset.run); }));
}

// --- live progress ------------------------------------------------------------------------------

async function openRun(rid) {
  if (S.es) { S.es.close(); S.es = null; }
  $("#runpanel").classList.remove("hidden");
  $("#console").innerHTML = "";
  S.run = rid; store.set("run", rid);
  await refreshRun();
  const es = new EventSource(`/api/runs/${encodeURIComponent(rid)}/events`);
  es.addEventListener("line", (ev) => appendLine(JSON.parse(ev.data)));
  es.addEventListener("status", () => refreshRun());
  es.addEventListener("end", () => { es.close(); if (S.es === es) S.es = null; });
  S.es = es;
  $("#runpanel").scrollIntoView({ behavior: "smooth", block: "start" });
}

const SIMPLE = new Set(["phase", "step", "check", "warn", "error", "tool"]);
function visible(kind) {
  if (S.mode === "simple") return SIMPLE.has(kind);
  if (SIMPLE.has(kind)) return true;
  const box = document.querySelector(`#detailFilters input[data-kind="${kind}"]`);
  return box ? box.checked : true;
}
function appendLine(e) {
  const c = $("#console"), div = document.createElement("div");
  div.className = `ln k-${e.kind}`; div.dataset.kind = e.kind;
  const text = e.kind === "step" ? e.text.replace(/▶ (\w+) \((\w+)\)/, (_, n) => `▶ ${stepTitle(n)}  [${n}]`) : e.text;
  div.innerHTML = `<span class="ts">${esc(e.ts.slice(11, 19))}</span> ${e.step && e.kind !== "step" ? `<span class="st">[${esc(e.step)}]</span> ` : ""}${esc(text)}`;
  if (!visible(e.kind)) div.classList.add("hidden");
  c.appendChild(div);
  if (c.childElementCount > 6000) c.firstElementChild.remove();
  if ($("#follow").checked) c.scrollTop = c.scrollHeight;
}
function applyFilters() { document.querySelectorAll("#console .ln").forEach((d) => d.classList.toggle("hidden", !visible(d.dataset.kind))); }
document.querySelectorAll(".seg-btn").forEach((b) => (b.onclick = () => {
  S.mode = b.dataset.mode; store.set("consoleMode", S.mode);
  document.querySelectorAll(".seg-btn").forEach((x) => x.classList.toggle("on", x === b));
  $("#detailFilters").classList.toggle("hidden", S.mode !== "detailed"); applyFilters();
}));
document.querySelectorAll("#detailFilters input").forEach((x) => x.addEventListener("change", applyFilters));

const dur = (a, b) => { if (!a) return ""; const s = Math.max(0, Math.round(((b ? new Date(b) : new Date()) - new Date(a)) / 1000)); return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`; };

async function refreshRun() {
  if (!S.run) return;
  const r = await api(`/api/runs/${encodeURIComponent(S.run)}`);
  S.runData = r;
  const tokens = r.steps.reduce((a, s) => a + s.input_tokens + s.output_tokens, 0);
  const reported = r.steps.some((s) => s.tokens_reported);
  const done = r.steps.filter((s) => ["ok", "skipped"].includes(s.status)).length;
  const statusText = { queued: "starting", running: "running", awaiting_review: "waiting for your review", completed: "finished", failed: "stopped on a problem", stopped: "stopped by you", interrupted: "interrupted (Studio was restarted)", rejected: "rejected" }[r.status] || r.status;
  $("#runtitle").textContent = `${r.kind === "analysis" ? "Analysis" : "Build"} of ${r.story_id}: ${statusText}`;
  $("#runmeta").textContent = [`${done} of ${r.steps.length} steps done`, r.branch && `branch ${r.branch}`,
    `Kiro usage ≈ ${fmt(tokens)} tokens${reported ? "" : " (estimated)"}`, `started ${ago(r.created_at)}`].filter(Boolean).join(" · ");

  const cur = r.steps.find((s) => s.status === "running");
  const now = $("#nowLine");
  if (r.active && cur) { now.classList.remove("hidden"); now.innerHTML = `<span class="spin" aria-hidden="true"></span><b>Now:</b> ${esc(stepTitle(cur.name))} — ${esc((STEP_INFO[cur.name] || ["", ""])[1])} <span class="muted small" id="nowDur">(${dur(cur.started_at)})</span>`; }
  else now.classList.add("hidden");

  const failed = r.steps.find((s) => s.status === "failed");
  let alert = "";
  if (r.status === "failed" && failed) alert = `<div class="callout bad"><b>Stopped at "${esc(stepTitle(failed.name))}".</b> ${esc(failureHint(failed.name, failed.detail))}</div>`;
  else if (r.status === "failed") alert = `<div class="callout bad"><b>The run failed.</b> ${esc(r.error || "")}</div>`;
  else if (r.status === "stopped") alert = `<div class="callout warn"><b>You stopped this run.</b> Resume continues from the step that was interrupted.</div>`;
  else if (r.status === "interrupted") alert = `<div class="callout warn"><b>Studio was restarted while this was running.</b> Resume to continue from where it stopped.</div>`;
  else if (r.status === "awaiting_review") alert = `<div class="callout"><b>Your turn.</b> Kiro committed the change on <code>${esc(r.branch)}</code>. <a href="#" id="goReview">Review it now</a>.</div>`;
  else if (r.status === "completed" && r.kind === "analysis") alert = `<div class="callout ok"><b>Analysis finished: ${r.confidence}% confidence.</b> <a href="#" id="goAnalysis">See the result</a>.</div>`;
  else if (r.status === "completed") alert = `<div class="callout ok"><b>Approved.</b> <a href="#" id="goShip">Push and open a pull request</a>.</div>`;
  else if (r.status === "rejected") alert = `<div class="callout bad"><b>Rejected.</b> The commits stay on <code>${esc(r.branch)}</code>.</div>`;
  $("#runAlert").innerHTML = alert;
  const link = (id, view) => { const el = $(id); if (el) el.onclick = async (e) => { e.preventDefault(); if (S.story?.summary.id !== r.story_id) await openStory(r.story_id, view); else go(view); }; };
  link("#goReview", "review"); link("#goAnalysis", "analyze"); link("#goShip", "ship");

  $("#timeline").innerHTML = r.steps.map((s, k) => {
    const icon = { ok: "✓", skipped: "–", failed: "✗", running: "•" }[s.status] || k + 1;
    const info = STEP_INFO[s.name] || [s.name, ""];
    const detail = s.status === "skipped" ? (s.detail || "").replace(/^skipped:\s*/i, "Skipped: ") : ["ok", "failed"].includes(s.status) ? s.detail : info[1];
    return `<li class="tl ${esc(s.status)}"><span class="ti" aria-hidden="true">${icon}</span>
      <div><span class="tn">${esc(info[0])}</span><span class="tt">${esc(s.name)}</span><div class="td">${esc((detail || "").split("\n")[0].slice(0, 260))}</div></div>
      <span class="tk">${s.started_at ? dur(s.started_at, s.ended_at) : ""}${s.kind === "agent" && (s.input_tokens || s.output_tokens) ? `<br>≈${fmt(s.input_tokens + s.output_tokens)} tok` : ""}</span></li>`;
  }).join("");

  $("#btnStop").classList.toggle("hidden", !r.active);
  const canResume = !r.active && ["failed", "stopped", "interrupted"].includes(r.status);
  const canRerun = !r.active && ["failed", "stopped", "interrupted", "awaiting_review"].includes(r.status);
  $("#btnResume").classList.toggle("hidden", !canResume);
  $("#restartBox").classList.toggle("hidden", !canRerun);
  if (canRerun) $("#fromStep").innerHTML = r.steps.filter((s) => s.kind !== "human").map((s) => `<option value="${esc(s.name)}" ${failed && failed.name === s.name ? "selected" : ""}>${esc(stepTitle(s.name))}</option>`).join("");
  if (!r.active) { loadOverview(); if (S.story?.summary.id === r.story_id) refreshStory(); }
}
const resumeRun = async (from_step) => {
  try { await api(`/api/runs/${S.run}/resume`, { method: "POST", body: JSON.stringify({ from_step: from_step || "" }) }); await openRun(S.run); if (S.story) refreshStory(); }
  catch (e) { toast(e.message); }
};
$("#btnStop").onclick = async () => { if (!confirm("Stop this run? You can resume it later from the same step.")) return; try { await api(`/api/runs/${S.run}/stop`, { method: "POST" }); } catch (e) { toast(e.message); } };
$("#btnResume").onclick = () => resumeRun("");
$("#btnRestart").onclick = () => { const s = $("#fromStep").value; if (confirm(`Run "${stepTitle(s)}" and every step after it again? Commits already made stay on the branch.`)) resumeRun(s); };
setInterval(() => { const r = S.runData; if (r?.active) { const cur = r.steps.find((s) => s.status === "running"); const sp = $("#nowDur"); if (cur && sp) sp.textContent = `(${dur(cur.started_at)})`; } }, 1000);

function colorDiff(text) {
  return text.split("\n").map((l) => {
    const c = l.startsWith("+") && !l.startsWith("+++") ? "a" : l.startsWith("-") && !l.startsWith("---") ? "d" : /^(## |@@|diff --git)/.test(l) ? "h" : "";
    return `<span class="${c}">${esc(l)}</span>`;
  }).join("\n");
}

// --- boot -----------------------------------------------------------------------------------------

function renderWelcome() {
  $("#workspace").innerHTML = `<div class="welcome"><h1>Welcome to Harness Studio</h1>
    <p class="muted">Pick a story on the left, or start with the suggested one. Each story goes through five stages:</p>
    <ol><li><b>Understand</b> what it asks and what it needs.</li><li><b>Analyze</b>: Kiro checks it can be built (confidence score).</li><li><b>Implement</b>: Kiro plans, tests, codes and commits on a new branch while you watch.</li><li><b>Review</b> the change yourself.</li><li><b>Ship</b>: push, open a pull request, record it as done.</li></ol>
    <div class="row"><button class="btn primary" id="wNext" ${S.ov.next ? "" : "disabled"}>Open the suggested story</button><button class="btn" id="wHelp">How it works</button><button class="btn" id="wSetup">Check setup</button></div></div>`;
  $("#wNext").onclick = () => openStory(S.ov.next);
  $("#wHelp").onclick = openHelp;
  $("#wSetup").onclick = openSetup;
}

(async function boot() {
  S.mode = store.get("consoleMode") === "detailed" ? "detailed" : "simple";
  document.querySelectorAll(".seg-btn").forEach((x) => x.classList.toggle("on", x.dataset.mode === S.mode));
  $("#detailFilters").classList.toggle("hidden", S.mode !== "detailed");
  try {
    await loadOverview();
    // Links: ?story=F02-S02&view=analyze&run=<id>&panel=help|setup
    const q = new URLSearchParams(location.search);
    const sid = q.get("story") || store.get("story");
    const view = ["understand", "analyze", "implement", "review", "ship", "history"].includes(q.get("view")) ? q.get("view") : null;
    if (sid && S.ov.stories.some((s) => s.id === sid)) await openStory(sid, view);
    else renderWelcome();
    if (q.get("panel") === "help") openHelp();
    else if (q.get("panel") === "setup") openSetup();
    else if (setupChecks().some((c) => !c.ok && !c.soft) && !store.get("setupSeen")) { store.set("setupSeen", "1"); openSetup(); }
    const rid = q.get("run") || S.ov.active_run;
    if (rid && rid !== S.run) await openRun(rid).catch(() => {});
  } catch (e) { $("#workspace").innerHTML = `<div class="callout bad"><b>Studio could not load.</b> ${esc(e.message)}. Check that the server is still running in your terminal.</div>`; }
  setInterval(() => { if (!S.ov?.active_run) loadOverview().catch(() => {}); }, 20000);
})();
