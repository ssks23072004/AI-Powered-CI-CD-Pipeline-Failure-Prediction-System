// ════════════════════════════════
//  TABS
// ════════════════════════════════
let lastGithubResults = null;
let lastGithubRepo    = null;
let lastGithubToken   = null;

// ✅ Polling interval handles
let analyticsInterval = null;
let githubInterval    = null;

function showTab(name) {
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  document.getElementById("tab-" + name).classList.add("active");
  document.querySelectorAll(".nav-item").forEach(n => {
    if (n.getAttribute("onclick") === `showTab('${name}')`)
      n.classList.add("active");
  });

  // ✅ Stop all polling when switching away
  clearInterval(analyticsInterval);
  clearInterval(githubInterval);

  if (name === "analytics") {
    loadSummary();
    setTimeout(() => loadAnalyticsCharts(), 80);
    // ✅ Auto-refresh analytics every 10 seconds
    analyticsInterval = setInterval(() => {
      loadSummary();
      loadAnalyticsCharts();
    }, 10000);
  }

  if (name === "history") { loadAllHistory(); }
  if (name === "models")  { setTimeout(() => loadModelStats(), 80); }

  if (name === "github") {
    // ✅ Restore last GitHub results on tab switch
    if (lastGithubResults) {
      setTimeout(() => {
        buildGithubCharts(lastGithubResults);
        buildGithubTable(lastGithubResults);
        document.getElementById("github-charts").style.display = "block";
        const failures = lastGithubResults.filter(r => r.probability > 0.5).length;
        const color    = failures > 0 ? "var(--danger)" : "var(--success)";
        document.getElementById("github-result").innerHTML = `
          <span style="color:${color}; font-weight:700;">
            📊 ${failures} of ${lastGithubResults.length} recent runs predicted as FAILURE RISK
          </span>
          <span style="color:var(--muted); font-size:0.82rem; margin-left:12px;">
            Repo: ${lastGithubRepo}
          </span>
          <span id="github-refresh-badge"
                style="color:var(--muted); font-size:0.75rem; margin-left:8px;">
            🔄 auto-refreshing every 30s
          </span>`;
      }, 80);
    }

    // ✅ Auto-refresh GitHub every 30 seconds if a repo is loaded
    if (lastGithubRepo) {
      githubInterval = setInterval(() => {
        if (lastGithubRepo) refreshGitHub(lastGithubToken);
      }, 30000);
    }
  }
}

// ════════════════════════════════
//  CHART INSTANCES
// ════════════════════════════════
let trendChart        = null;
let doughnutChart     = null;
let barChart          = null;
let errorDistChart    = null;
let githubTrendChart  = null;
let githubDoughChart  = null;
let modelAccChart     = null;
let modelRadarChart   = null;
let modelF1Chart      = null;
let modelPRChart      = null;

Chart.defaults.color           = "#64748b";
Chart.defaults.borderColor     = "#2a2d3e";
Chart.defaults.backgroundColor = "transparent";

// ════════════════════════════════
//  PREDICT
// ════════════════════════════════
async function predict() {
  const error      = document.getElementById("error").value;
  const warning    = document.getElementById("warning").value;
  const dependency = document.getElementById("dependency").value;
  const install    = document.getElementById("install").value;
  const clone      = document.getElementById("clone").value;

  if (error === "" || warning === "" || dependency === "" || install === "") {
    alert("Please fill in all fields");
    return;
  }

  const btn = document.querySelector(".btn-primary");
  btn.textContent = "⏳ Predicting…";
  btn.disabled    = true;

  try {
    const res = await fetch("/predict", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        error_count:          parseInt(error),
        warning_count:        parseInt(warning),
        dependency_downloads: parseInt(dependency),
        install_steps:        parseInt(install),
        has_git_clone:        parseInt(clone)
      })
    });

    const data = await res.json();
    if (data.error) { alert("Error: " + data.error); return; }
    showResult(data);

  } catch (err) {
    alert("Network error. Is the server running?");
    console.error(err);
  } finally {
    btn.textContent = "⚡ Run Prediction";
    btn.disabled    = false;
  }
}

function showResult(data) {
  document.getElementById("result-placeholder").style.display = "none";
  document.getElementById("result-content").style.display     = "block";

  const prob   = data.probability;
  const isRisk = data.alert === "FAILURE RISK";
  const verdict = document.getElementById("result-verdict");
  verdict.className = "verdict-box " + (isRisk ? "failure" : "success");
  verdict.innerHTML = `
    ${isRisk ? "🔴 FAILURE RISK" : "🟢 PIPELINE SAFE"}
    <div style="font-size:0.85rem; font-weight:400; margin-top:6px; opacity:0.8;">
      Model confidence: ${(Math.max(prob, 1 - prob) * 100).toFixed(1)}%
    </div>`;

  const pct = (prob * 100).toFixed(1);
  document.getElementById("prob-value").textContent = pct + "%";
  document.getElementById("prob-bar").style.width   = pct + "%";

  const bd = data.breakdown || {};
  setBar("error",      bd.error_risk      || 0);
  setBar("warning",    bd.warning_risk    || 0);
  setBar("complexity", bd.complexity_risk || 0);
  setBar("history",    bd.history_risk    || 0);

  const list = document.getElementById("suggestions-list");
  list.innerHTML = "";
  (data.suggestions || []).forEach(s => {
    const div = document.createElement("div");
    div.className = `suggestion-item ${s.level}`;
    div.innerHTML = `
      <div class="suggestion-icon">${s.icon}</div>
      <div>
        <div class="suggestion-title">${s.title}</div>
        <div>${s.message}</div>
      </div>`;
    list.appendChild(div);
  });

  // -----------------------------
  // 🔍 EXPLANATION RENDER (NEW)
  // -----------------------------
  const explanationBox = document.getElementById("explanation-box");
  if (explanationBox) {
    if (data.explanation && data.explanation.length > 0) {
      explanationBox.innerHTML = data.explanation
        .map(e => `
  <div style="display:flex; gap:8px; align-items:flex-start;">
    <span style="color:#f59e0b;">●</span>
    <span>${e}</span>
  </div>
`)
        .join("");
    } else {
      explanationBox.innerHTML = "<div>Pipeline looks stable.</div>";
    }
  }
}

function setBar(id, value) {
  document.getElementById("b-"  + id).style.width = value + "%";
  document.getElementById("bv-" + id).textContent  = value + "%";
}

// ════════════════════════════════
//  SUMMARY STATS
// ════════════════════════════════
async function loadSummary() {
  try {
    const res  = await fetch("/summary");
    const data = await res.json();
    document.getElementById("st-total").textContent    = data.total       || 0;
    document.getElementById("st-failures").textContent = data.failures    || 0;
    document.getElementById("st-safe").textContent     = data.safe        || 0;
    document.getElementById("st-rate").textContent     = (data.failure_rate || 0) + "%";
    document.getElementById("st-avgprob").textContent  = (data.avg_prob   || 0) + "%";
  } catch (err) {
    console.error("Summary error:", err);
  }
}

// ════════════════════════════════
//  ANALYTICS CHARTS
// ════════════════════════════════
async function loadAnalyticsCharts() {
  try {
    const res  = await fetch("/history/all");
    const rows = await res.json();

    if (!Array.isArray(rows) || rows.length === 0) return;

    const labels      = rows.map((_, i) => "Run " + (rows.length - i));
    const probs       = rows.map(r => parseFloat(r.probability));
    const predictions = rows.map(r => r.prediction);
    const errors      = rows.map(r => r.error_count);

    const failures = predictions.filter(p => p === 1).length;
    const safe     = predictions.filter(p => p === 0).length;

    buildTrendChart(labels.slice().reverse(), probs.slice().reverse());
    buildDoughnutChart(failures, safe);
    buildBarChart(probs);
    buildErrorDistChart(errors);

  } catch (err) {
    console.error("Analytics error:", err);
  }
}

// 1. Line — Probability Trend
function buildTrendChart(labels, data) {
  const ctx = document.getElementById("trendChart");
  if (!ctx) return;
  if (trendChart) trendChart.destroy();
  trendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Failure Probability",
        data,
        borderColor:     "#6c63ff",
        backgroundColor: "rgba(108,99,255,0.08)",
        borderWidth: 2,
        tension: 0.4,
        fill: true,
        pointRadius: 4,
        pointBackgroundColor: data.map(p => p > 0.5 ? "#ef4444" : "#22c55e")
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: {
          min: 0, max: 1,
          ticks: { callback: v => (v * 100).toFixed(0) + "%" }
        }
      }
    }
  });
}

// 2. Doughnut — Failure vs Safe
function buildDoughnutChart(failures, safe) {
  const ctx = document.getElementById("doughnutChart");
  if (!ctx) return;
  if (doughnutChart) doughnutChart.destroy();
  doughnutChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Failure Risk", "Safe"],
      datasets: [{
        data: [failures, safe],
        backgroundColor: ["rgba(239,68,68,0.8)", "rgba(34,197,94,0.8)"],
        borderColor:     ["#ef4444", "#22c55e"],
        borderWidth: 2,
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "65%",
      plugins: { legend: { position: "bottom" } }
    }
  });
}

// 3. Bar — Distribution buckets
function buildBarChart(probs) {
  const ctx = document.getElementById("barChart");
  if (!ctx) return;
  if (barChart) barChart.destroy();

  const buckets = [0, 0, 0, 0, 0];
  probs.forEach(p => {
    const i = Math.min(Math.floor(p * 5), 4);
    buckets[i]++;
  });

  barChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["0–20%", "20–40%", "40–60%", "60–80%", "80–100%"],
      datasets: [{
        label: "Number of Runs",
        data: buckets,
        backgroundColor: [
          "rgba(34,197,94,0.7)",
          "rgba(132,225,188,0.7)",
          "rgba(245,158,11,0.7)",
          "rgba(249,115,22,0.7)",
          "rgba(239,68,68,0.7)",
        ],
        borderColor:  ["#22c55e","#84e1bc","#f59e0b","#f97316","#ef4444"],
        borderWidth:  2,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { stepSize: 1 } },
        x: { title: { display: true, text: "Failure Probability Range" } }
      }
    }
  });
}

// 4. Horizontal Bar — Error Count Distribution
function buildErrorDistChart(errors) {
  const ctx = document.getElementById("errorDistChart");
  if (!ctx) return;
  if (errorDistChart) errorDistChart.destroy();

  const counts = {};
  errors.forEach(e => { counts[e] = (counts[e] || 0) + 1; });
  const sorted = Object.keys(counts).sort((a, b) => a - b);

  errorDistChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: sorted.map(k => `${k} error${k == 1 ? "" : "s"}`),
      datasets: [{
        label: "Run Count",
        data: sorted.map(k => counts[k]),
        backgroundColor: sorted.map(k =>
          k >= 3 ? "rgba(239,68,68,0.7)" :
          k >= 1 ? "rgba(245,158,11,0.7)" :
                   "rgba(34,197,94,0.7)"
        ),
        borderRadius: 6,
        borderWidth:  0
      }]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { beginAtZero: true, ticks: { stepSize: 1 } } }
    }
  });
}

// ════════════════════════════════
//  HISTORY ANALYSER
// ════════════════════════════════
async function loadAllHistory() {
  try {
    const res  = await fetch("/history/all");
    let   rows = await res.json();

    if (!Array.isArray(rows)) {
      document.getElementById("history-tbody").innerHTML =
        `<tr><td colspan="9"
          style="text-align:center;color:var(--muted);padding:30px;">
          Error loading history. Try refreshing.
        </td></tr>`;
      document.getElementById("history-count").textContent = "Showing 0 records";
      return;
    }

    if (rows.length === 0) {
      document.getElementById("history-tbody").innerHTML =
        `<tr><td colspan="9"
          style="text-align:center;color:var(--muted);padding:30px;">
          No predictions yet. Run a prediction first.
        </td></tr>`;
      document.getElementById("history-count").textContent = "Showing 0 records";
      return;
    }

    const filterVal = document.getElementById("filter-result").value;
    if (filterVal === "failure") rows = rows.filter(r => r.prediction === 1);
    if (filterVal === "safe")    rows = rows.filter(r => r.prediction === 0);

    const sortVal = document.getElementById("filter-sort").value;
    if (sortVal === "oldest")  rows = rows.slice().reverse();
    if (sortVal === "highest") rows = rows.slice().sort((a, b) => b.probability - a.probability);
    if (sortVal === "lowest")  rows = rows.slice().sort((a, b) => a.probability - b.probability);

    document.getElementById("history-count").textContent =
      `Showing ${rows.length} record${rows.length !== 1 ? "s" : ""}`;

    const tbody = document.getElementById("history-tbody");
    tbody.innerHTML = "";

    rows.forEach(r => {
      const prob   = parseFloat(r.probability);
      const isRisk = r.prediction === 1;
      const badge  = isRisk
        ? `<span class="badge badge-failure">🔴 FAILURE</span>`
        : `<span class="badge badge-safe">🟢 SAFE</span>`;

      const probColor =
        prob >= 0.8 ? "#ef4444" :
        prob >= 0.5 ? "#f59e0b" :
        prob >= 0.2 ? "#84e1bc" : "#22c55e";

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="color:var(--muted)">${r.id}</td>
        <td style="color:var(--muted);font-size:0.78rem;">${r.timestamp || "—"}</td>
        <td><span style="color:${r.error_count   >= 3 ? "#ef4444" : "var(--text)"}">
          ${r.error_count}</span></td>
        <td><span style="color:${r.warning_count >= 5 ? "#f59e0b" : "var(--text)"}">
          ${r.warning_count}</span></td>
        <td>${r.dependency_downloads}</td>
        <td>${r.install_steps}</td>
        <td>${r.has_git_clone}</td>
        <td><span style="color:${probColor}; font-weight:700;">
          ${(prob * 100).toFixed(1)}%</span></td>
        <td>${badge}</td>`;
      tbody.appendChild(tr);
    });

  } catch (err) {
    console.error("History error:", err);
  }
}

// ════════════════════════════════
//  GITHUB PREDICTION
// ════════════════════════════════
async function predictGitHub() {
  const repo     = document.getElementById("repo").value.trim();
  const token = document.getElementById("token").value.trim();
  const resultEl = document.getElementById("github-result");

  if (!repo) {
    alert("Please enter a repository (e.g. tensorflow/tensorflow)");
    return;
  }
  if (!repo.includes("/")) {
    alert("Format must be owner/repo  (e.g. tensorflow/tensorflow)");
    return;
  }

  // ✅ Stop any existing GitHub polling before new fetch
  clearInterval(githubInterval);

  resultEl.innerHTML =
    `<span style="color:var(--muted)">⏳ Fetching GitHub workflow data…</span>`;
  document.getElementById("github-charts").style.display = "none";
  lastGithubResults = null;
  lastGithubRepo    = null;
  lastGithubToken   = token;

  await fetchGithubData(repo, token);

  // ✅ Start real-time polling every 30 seconds
  githubInterval = setInterval(() => refreshGitHub(token), 30000);
}

// ── Shared fetch used by both initial load and polling ──
async function fetchGithubData(repo, token = null) {
  const resultEl = document.getElementById("github-result");
  try {
    const res  = await fetch("/github_predict", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        repo: repo,
        token: token || null
      })
    });
    const data = await res.json();

    if (data.error) {
      resultEl.innerHTML =
        `<span style="color:var(--danger)">⚠️ ${data.error}</span>`;
      clearInterval(githubInterval);
      return;
    }

    if (!data.results || data.results.length === 0) {
      resultEl.innerHTML =
        `<span style="color:var(--warning)">⚠️ No workflow runs found.</span>`;
      return;
    }

    const results  = data.results;
    const failures = results.filter(r => r.probability > 0.5).length;
    const color    = failures > 0 ? "var(--danger)" : "var(--success)";
    const now      = new Date().toLocaleTimeString();

    resultEl.innerHTML = `
      <span style="color:${color}; font-weight:700;">
        📊 ${failures} of ${results.length} recent runs predicted as FAILURE RISK
      </span>
      <span style="color:var(--muted); font-size:0.82rem; margin-left:12px;">
        Repo: ${data.repo}
      </span>
      <span style="color:var(--muted); font-size:0.75rem; margin-left:12px;">
        🔄 Last updated: ${now} · auto-refreshing every 30s
      </span>`;

    // ✅ Store for tab persistence and polling
    lastGithubResults = results;
    lastGithubRepo    = data.repo;

    document.getElementById("github-charts").style.display = "block";
    buildGithubCharts(results);
    buildGithubTable(results);

  } catch (err) {
    resultEl.innerHTML =
      `<span style="color:var(--danger)">⚠️ Network error.</span>`;
    console.error(err);
  }
}

// ✅ Silent background refresh — no loading spinner
async function refreshGitHub(token = null) {
  if (!lastGithubRepo) return;
  await fetchGithubData(lastGithubRepo,token);
}

function buildGithubCharts(results) {
  const labels = results.map(r => r.run_name || "Run");
  const probs  = results.map(r => parseFloat(r.probability));

  const ctx1 = document.getElementById("githubTrendChart");
  if (githubTrendChart) githubTrendChart.destroy();
  githubTrendChart = new Chart(ctx1, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Failure Probability",
        data: probs,
        borderColor:     "#f59e0b",
        backgroundColor: "rgba(245,158,11,0.08)",
        borderWidth: 2,
        tension: 0.4,
        fill: true,
        pointRadius: 6,
        pointBackgroundColor: probs.map(p => p > 0.5 ? "#ef4444" : "#22c55e")
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          min: 0, max: 1,
          ticks: { callback: v => (v * 100).toFixed(0) + "%" }
        }
      }
    }
  });

  const statusCounts = {};
  results.forEach(r => {
    const s = r.conclusion || r.status || "unknown";
    statusCounts[s] = (statusCounts[s] || 0) + 1;
  });

  const statusColors = {
    success:   "#22c55e",
    failure:   "#ef4444",
    cancelled: "#f59e0b",
    skipped:   "#64748b",
    unknown:   "#94a3b8",
  };

  const ctx2 = document.getElementById("githubDoughnutChart");
  if (githubDoughChart) githubDoughChart.destroy();
  githubDoughChart = new Chart(ctx2, {
    type: "doughnut",
    data: {
      labels: Object.keys(statusCounts),
      datasets: [{
        data: Object.values(statusCounts),
        backgroundColor: Object.keys(statusCounts).map(
          k => statusColors[k] || "#94a3b8"
        ),
        borderWidth: 2,
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "60%",
      plugins: { legend: { position: "bottom" } }
    }
  });
}

function buildGithubTable(results) {
  const tbody = document.getElementById("github-tbody");
  tbody.innerHTML = "";
  results.forEach((r, i) => {
    const prob   = parseFloat(r.probability);
    const isRisk = prob > 0.5;
    const badge  = isRisk
      ? `<span class="badge badge-failure">🔴 FAILURE</span>`
      : `<span class="badge badge-safe">🟢 SAFE</span>`;

    const statusBadge =
      r.conclusion === "success"
        ? `<span class="badge badge-safe">${r.conclusion}</span>`
      : r.conclusion === "failure"
        ? `<span class="badge badge-failure">${r.conclusion}</span>`
        : `<span class="badge badge-unknown">
            ${r.conclusion || r.status || "unknown"}
           </span>`;

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="color:var(--muted)">${i + 1}</td>
      <td>${r.run_name || "Workflow Run"}</td>
      <td>${statusBadge}</td>
      <td style="font-weight:700; color:${isRisk ? "#ef4444" : "#22c55e"}">
        ${(prob * 100).toFixed(1)}%
      </td>
      <td>${badge}</td>`;
    tbody.appendChild(tr);
  });
}

// ════════════════════════════════
//  MODEL STATS
// ════════════════════════════════
async function loadModelStats() {
  try {
    const res  = await fetch("/model-stats");
    const data = await res.json();

    if (data.error) {
      document.getElementById("model-error").style.display   = "block";
      document.getElementById("model-content").style.display = "none";
      return;
    }

    document.getElementById("m-best").textContent     = data.best_model     || "—";
    document.getElementById("m-acc").textContent      = (data.best_accuracy || 0) + "%";
    document.getElementById("m-dataset").textContent  = data.dataset_size   || "—";
    document.getElementById("m-failrate").textContent = (data.failure_rate  || 0) + "%";

    const models     = data.models || {};
    const names      = Object.keys(models);
    const shortNames = names.map(n =>
      n.replace("Random Forest",       "RF")
       .replace("Logistic Regression", "LR")
       .replace("Decision Tree",       "DT")
       .replace("Gradient Boosting",   "GB")
    );

    const accuracy  = names.map(n => models[n].accuracy);
    const precision = names.map(n => models[n].precision);
    const recall    = names.map(n => models[n].recall);
    const f1        = names.map(n => models[n].f1_score);

    // 1 ── Bar: Accuracy
    const ctx1 = document.getElementById("modelAccChart");
    if (modelAccChart) modelAccChart.destroy();
    modelAccChart = new Chart(ctx1, {
      type: "bar",
      data: {
        labels: shortNames,
        datasets: [{
          label: "Accuracy (%)",
          data: accuracy,
          backgroundColor: names.map(n =>
            n === data.best_model
              ? "rgba(108,99,255,0.85)"
              : "rgba(108,99,255,0.35)"
          ),
          borderColor:  "#6c63ff",
          borderWidth:  2,
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { min: 0, max: 100, ticks: { callback: v => v + "%" } } }
      }
    });

    // 2 ── Radar: All metrics
    const ctx2 = document.getElementById("modelRadarChart");
    if (modelRadarChart) modelRadarChart.destroy();
    const radarColors = [
      "rgba(108,99,255,0.5)",
      "rgba(34,197,94,0.5)",
      "rgba(245,158,11,0.5)",
      "rgba(239,68,68,0.5)"
    ];
    modelRadarChart = new Chart(ctx2, {
      type: "radar",
      data: {
        labels: ["Accuracy", "Precision", "Recall", "F1 Score"],
        datasets: names.map((n, i) => ({
          label: shortNames[i],
          data: [
            models[n].accuracy,
            models[n].precision,
            models[n].recall,
            models[n].f1_score
          ],
          backgroundColor: radarColors[i],
          borderColor:     radarColors[i].replace("0.5", "1"),
          borderWidth: 2,
          pointRadius: 4
        }))
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          r: {
            min: 0, max: 100,
            ticks: { stepSize: 20, callback: v => v + "%" }
          }
        },
        plugins: { legend: { position: "bottom" } }
      }
    });

    // 3 ── Horizontal Bar: F1 Ranking
    const sorted = names
      .map((n, i) => ({ name: shortNames[i], f1: models[n].f1_score }))
      .sort((a, b) => b.f1 - a.f1);

    const ctx3 = document.getElementById("modelF1Chart");
    if (modelF1Chart) modelF1Chart.destroy();
    modelF1Chart = new Chart(ctx3, {
      type: "bar",
      data: {
        labels: sorted.map(s => s.name),
        datasets: [{
          label: "F1 Score (%)",
          data:  sorted.map(s => s.f1),
          backgroundColor: [
            "rgba(108,99,255,0.85)",
            "rgba(108,99,255,0.6)",
            "rgba(108,99,255,0.4)",
            "rgba(108,99,255,0.25)"
          ],
          borderRadius: 6,
          borderWidth:  0
        }]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { x: { min: 0, max: 100, ticks: { callback: v => v + "%" } } }
      }
    });

    // 4 ── Grouped Bar: Precision vs Recall
    const ctx4 = document.getElementById("modelPRChart");
    if (modelPRChart) modelPRChart.destroy();
    modelPRChart = new Chart(ctx4, {
      type: "bar",
      data: {
        labels: shortNames,
        datasets: [
          {
            label: "Precision (%)",
            data: precision,
            backgroundColor: "rgba(34,197,94,0.7)",
            borderColor:     "#22c55e",
            borderWidth:  2,
            borderRadius: 4
          },
          {
            label: "Recall (%)",
            data: recall,
            backgroundColor: "rgba(59,130,246,0.7)",
            borderColor:     "#3b82f6",
            borderWidth:  2,
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "bottom" } },
        scales: { y: { min: 0, max: 100, ticks: { callback: v => v + "%" } } }
      }
    });

  } catch (err) {
    console.error("Model stats error:", err);
  }
}

// ════════════════════════════════
//  ON LOAD
// ════════════════════════════════
window.onload = () => {
  loadSummary();
  setTimeout(() => loadAnalyticsCharts(), 80);
};