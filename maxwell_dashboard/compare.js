function getPath(obj, path) {
  if (!obj) return undefined;
  const parts = path.split(".");
  let cur = obj;
  for (const p of parts) {
    if (cur && Object.prototype.hasOwnProperty.call(cur, p)) cur = cur[p];
    else return undefined;
  }
  return cur;
}

function num(x) {
  if (x === null || x === undefined) return null;
  const n = Number(x);
  return Number.isFinite(n) ? n : null;
}

function fmt(x, decimals) {
  const n = num(x);
  if (n === null) return "—";
  if (decimals === undefined) return String(n);
  return n.toFixed(decimals);
}

function setStatus(text) {
  const el = document.getElementById("status");
  if (el) el.textContent = text;
}

async function readJsonFile(file) {
  const txt = await file.text();
  return JSON.parse(txt);
}

function metricRow(metric, a, b, deltaText, cls) {
  const tr = document.createElement("tr");
  if (cls) tr.className = cls;
  const td0 = document.createElement("td");
  td0.textContent = metric;
  const td1 = document.createElement("td");
  td1.textContent = a;
  const td2 = document.createElement("td");
  td2.textContent = b;
  const td3 = document.createElement("td");
  td3.textContent = deltaText;
  tr.appendChild(td0);
  tr.appendChild(td1);
  tr.appendChild(td2);
  tr.appendChild(td3);
  return tr;
}

function classify(delta, betterWhen) {
  if (delta === null) return "";
  if (betterWhen === "lower") {
    if (delta < 0) return "win";
    if (delta > 0) return "lose";
    return "tie";
  }
  if (betterWhen === "higher") {
    if (delta > 0) return "win";
    if (delta < 0) return "lose";
    return "tie";
  }
  return "";
}

function render(a, b) {
  const tbody = document.querySelector("#cmpTable tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  // Prefer Pack Standard v1 metrics if present.
  const hasMetricsV1 = (x) => x && typeof x === "object" && x.schema === "sigma_summary_public_v1" && x.metrics;

  function v1(x, which, key) {
    if (!hasMetricsV1(x)) return null;
    const m = x.metrics?.[which]?.[key];
    return num(m);
  }

  const rows = [
    {
      label: "GPU name",
      a: String(getPath(a, "gpu.name") ?? "—"),
      b: String(getPath(b, "gpu.name") ?? "—"),
      delta: null,
      betterWhen: "none",
    },
    {
      label: "CTDR/Omega QPS",
      path: "measured.ctdr.qps",
      v1: { which: "omega", key: "qps" },
      fmtDec: 3,
      betterWhen: "higher",
    },
    {
      label: "CTDR/Omega latency p95 (ms)",
      path: "measured.ctdr.latency_ms.p95",
      v1: { which: "omega", key: "lat_p95_ms" },
      fmtDec: 3,
      betterWhen: "lower",
    },
    {
      label: "CTDR/Omega J/query",
      path: "measured.ctdr.energy.joules_per_query",
      v1: { which: "omega", key: "joules_per_query" },
      fmtDec: 3,
      betterWhen: "lower",
    },
    {
      label: "CTDR/Omega power avg (W)",
      path: "measured.ctdr.energy.power_w_avg",
      v1: { which: "omega", key: "power_w_avg" },
      fmtDec: 1,
      betterWhen: "lower",
    },
    {
      label: "CTDR/Omega GPU util avg (%)",
      path: "measured.ctdr.energy.gpu_util_pct_avg",
      v1: { which: "omega", key: "gpu_util_pct_avg" },
      fmtDec: 1,
      betterWhen: "higher",
    },
    {
      label: "CTDR/Omega top‑1 accuracy",
      path: "measured.ctdr.accuracy.top1_accuracy",
      v1: { which: "omega", key: "top1_accuracy" },
      fmtDec: 6,
      betterWhen: "higher",
    },
    {
      label: "Baseline vector_scan QPS",
      path: "measured.baseline_vector_scan.qps",
      v1: { which: "baseline", key: "qps" },
      fmtDec: 3,
      betterWhen: "higher",
    },
    {
      label: "Baseline vector_scan latency p95 (ms)",
      path: "measured.baseline_vector_scan.latency_ms.p95",
      v1: { which: "baseline", key: "lat_p95_ms" },
      fmtDec: 3,
      betterWhen: "lower",
    },
    {
      label: "Baseline vector_scan J/query",
      path: "measured.baseline_vector_scan.energy.joules_per_query",
      v1: { which: "baseline", key: "joules_per_query" },
      fmtDec: 3,
      betterWhen: "lower",
    },
    {
      label: "Baseline vector_scan power avg (W)",
      path: "measured.baseline_vector_scan.energy.power_w_avg",
      v1: { which: "baseline", key: "power_w_avg" },
      fmtDec: 1,
      betterWhen: "lower",
    },
    {
      label: "Baseline vector_scan GPU util avg (%)",
      path: "measured.baseline_vector_scan.energy.gpu_util_pct_avg",
      v1: { which: "baseline", key: "gpu_util_pct_avg" },
      fmtDec: 1,
      betterWhen: "higher",
    },
    {
      label: "Baseline vector_scan top‑1 accuracy",
      path: "measured.baseline_vector_scan.accuracy.top1_accuracy",
      v1: { which: "baseline", key: "top1_accuracy" },
      fmtDec: 6,
      betterWhen: "higher",
    },
  ];

  for (const r of rows) {
    if (!r.path) {
      tbody.appendChild(metricRow(r.label, r.a, r.b, "—", ""));
      continue;
    }
    const av = hasMetricsV1(a) && r.v1 ? v1(a, r.v1.which, r.v1.key) : num(getPath(a, r.path));
    const bv = hasMetricsV1(b) && r.v1 ? v1(b, r.v1.which, r.v1.key) : num(getPath(b, r.path));
    const delta = av !== null && bv !== null ? bv - av : null; // B - A
    const cls = classify(delta, r.betterWhen);
    const deltaText = delta === null ? "—" : (r.betterWhen === "lower" ? fmt(delta, r.fmtDec) : fmt(delta, r.fmtDec));
    tbody.appendChild(metricRow(r.label, fmt(av, r.fmtDec), fmt(bv, r.fmtDec), deltaText, cls));
  }

  // Quick "gate" hints
  const aAcc = hasMetricsV1(a) ? v1(a, "omega", "top1_accuracy") : num(getPath(a, "measured.ctdr.accuracy.top1_accuracy"));
  const bAcc = hasMetricsV1(b) ? v1(b, "omega", "top1_accuracy") : num(getPath(b, "measured.ctdr.accuracy.top1_accuracy"));
  if (aAcc !== null && aAcc < 1.0) tbody.appendChild(metricRow("Gate: A exactness", "FAIL (<1.0)", "", "", "warn"));
  if (bAcc !== null && bAcc < 1.0) tbody.appendChild(metricRow("Gate: B exactness", "", "FAIL (<1.0)", "", "warn"));
}

let packA = null;
let packB = null;

async function onPick(which, file) {
  try {
    const j = await readJsonFile(file);
    if (which === "A") packA = j;
    else packB = j;
    if (packA && packB) {
      setStatus("Loaded both packs. Delta is B − A.");
      render(packA, packB);
    } else {
      setStatus("Loaded one pack. Pick the second file to compare.");
    }
  } catch (e) {
    setStatus("Failed to parse JSON: " + String(e));
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const a = document.getElementById("fileA");
  const b = document.getElementById("fileB");
  if (a) a.addEventListener("change", (ev) => onPick("A", ev.target.files[0]));
  if (b) b.addEventListener("change", (ev) => onPick("B", ev.target.files[0]));
});


