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

function fmt(val, decimals) {
  if (val === null || val === undefined) return "—";
  const n = Number(val);
  if (Number.isNaN(n)) return String(val);
  if (decimals === undefined) return String(n);
  return n.toFixed(decimals);
}

function fillText(selector, text) {
  const el = document.querySelector(selector);
  if (!el) return;
  el.textContent = text;
}

function fillById(id, text) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
}

function _num(x) {
  if (x === null || x === undefined) return null;
  const n = Number(x);
  return Number.isFinite(n) ? n : null;
}

function _setBar(id, pct) {
  const el = document.getElementById(id);
  if (!el) return;
  const p = Math.max(0, Math.min(100, pct));
  el.style.width = `${p}%`;
}

function _setGate(id, status, extra) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.remove("pass", "fail", "warn");
  el.classList.add(status);
  el.textContent = extra ? `${status.toUpperCase()} — ${extra}` : status.toUpperCase();
}

function _safeArr(x) {
  return Array.isArray(x) ? x : null;
}

function _normalizeTempC(tempC) {
  // Map 20°C -> 0 and 90°C -> 100 (fixed range for engineering readability).
  if (tempC === null || tempC === undefined) return null;
  const t = Number(tempC);
  if (!Number.isFinite(t)) return null;
  const v = ((t - 20.0) / (90.0 - 20.0)) * 100.0;
  return Math.max(0, Math.min(100, v));
}

function _drawLine(ctx, xs, ys, color, width) {
  ctx.strokeStyle = color;
  ctx.lineWidth = width || 2;
  ctx.beginPath();
  let started = false;
  for (let i = 0; i < xs.length; i++) {
    const y = ys[i];
    if (y === null || y === undefined) {
      started = false;
      continue;
    }
    const x = xs[i];
    if (!started) {
      ctx.moveTo(x, y);
      started = true;
    } else {
      ctx.lineTo(x, y);
    }
  }
  ctx.stroke();
}

function renderTelemetry(s) {
  const canvas = document.getElementById("telemetryCanvas");
  if (!canvas) return;

  const trackSel = document.getElementById("telemetryTrack");
  const track = trackSel && trackSel.value ? trackSel.value : "omega";

  const pLimit = _num(getPath(s, "gpu.power_limit_w")) ?? 350.0;
  const tel = getPath(s, `telemetry.${track}.gpu`);
  if (!tel || typeof tel !== "object") {
    const ctx0 = canvas.getContext("2d");
    if (ctx0) {
      ctx0.clearRect(0, 0, canvas.width, canvas.height);
      ctx0.fillStyle = "rgba(255,255,255,.45)";
      ctx0.font = "14px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace";
      ctx0.fillText("telemetry missing (pack did not include timeseries)", 16, 32);
    }
    fillById("telemetryStatus", `telemetry: missing (${track})`);
    return;
  }

  const t_s = _safeArr(tel.t_s);
  const power_w = _safeArr(tel.power_w);
  if (!t_s || !power_w || t_s.length === 0 || power_w.length !== t_s.length) {
    fillById("telemetryStatus", `telemetry: invalid (${track})`);
    return;
  }

  const util = _safeArr(tel.gpu_util_pct);
  const temp = _safeArr(tel.temp_c);

  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Frame
  const W = canvas.width;
  const H = canvas.height;
  const padL = 44;
  const padR = 12;
  const padT = 14;
  const padB = 22;
  const iw = W - padL - padR;
  const ih = H - padT - padB;

  // Scale X by [t0..t1]
  const t0 = Number(t_s[0]);
  const t1 = Number(t_s[t_s.length - 1]);
  const dt = Math.max(1e-9, t1 - t0);

  const xs = new Array(t_s.length);
  const yUtil = new Array(t_s.length);
  const yPower = new Array(t_s.length);
  const yTemp = new Array(t_s.length);
  let failSegments = 0;

  for (let i = 0; i < t_s.length; i++) {
    const ti = Number(t_s[i]);
    const x = padL + ((ti - t0) / dt) * iw;
    xs[i] = x;

    const u = util && i < util.length ? _num(util[i]) : null;
    const p = _num(power_w[i]);
    const pPct = p !== null ? (p / pLimit) * 100.0 : null;
    const tc = temp && i < temp.length ? _normalizeTempC(temp[i]) : null;

    yUtil[i] = u === null ? null : padT + (1.0 - u / 100.0) * ih;
    yPower[i] = pPct === null ? null : padT + (1.0 - Math.max(0, Math.min(100, pPct)) / 100.0) * ih;
    yTemp[i] = tc === null ? null : padT + (1.0 - tc / 100.0) * ih;

    const utilFail = u !== null && u < 70.0;
    const powerWarn = pPct !== null && pPct > 85.0;
    if (utilFail || powerWarn) failSegments += 1;
  }

  // Background grid (0..100)
  ctx.strokeStyle = "rgba(255,255,255,.10)";
  ctx.lineWidth = 1;
  for (const yPct of [0, 25, 50, 70, 85, 100]) {
    const y = padT + (1.0 - yPct / 100.0) * ih;
    ctx.beginPath();
    ctx.moveTo(padL, y);
    ctx.lineTo(padL + iw, y);
    ctx.stroke();
    ctx.fillStyle = "rgba(255,255,255,.45)";
    ctx.font = "11px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace";
    ctx.fillText(String(yPct), 10, y + 4);
  }

  // Shading: mark time slices that violate util/power gate.
  // (Keep simple: per-sample vertical stripes with low alpha.)
  for (let i = 0; i < xs.length; i++) {
    const u = util && i < util.length ? _num(util[i]) : null;
    const p = _num(power_w[i]);
    const pPct = p !== null ? (p / pLimit) * 100.0 : null;
    const utilFail = u !== null && u < 70.0;
    const powerWarn = pPct !== null && pPct > 85.0;
    if (!utilFail && !powerWarn) continue;
    const x = xs[i];
    ctx.fillStyle = utilFail ? "rgba(255,59,59,.10)" : "rgba(255,196,0,.08)";
    ctx.fillRect(x, padT, 2, ih);
  }

  // Lines
  _drawLine(ctx, xs, yUtil, "rgba(26,108,255,.95)", 2.2);   // util (blue)
  _drawLine(ctx, xs, yPower, "rgba(255,122,89,.95)", 2.0);  // power% (red)
  _drawLine(ctx, xs, yTemp, "rgba(180,180,180,.80)", 1.6);  // temp normalized (gray)

  // Labels
  ctx.fillStyle = "rgba(255,255,255,.75)";
  ctx.font = "12px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace";
  ctx.fillText("util%", padL + 8, padT + 14);
  ctx.fillStyle = "rgba(255,122,89,.95)";
  ctx.fillText("power%lim", padL + 8, padT + 30);
  ctx.fillStyle = "rgba(180,180,180,.85)";
  ctx.fillText("temp(norm)", padL + 8, padT + 46);

  fillById("telemetryStatus", `telemetry: ${track} | points=${t_s.length} | window=${dt.toFixed(1)}s | flagged=${failSegments}`);
}

function renderSummary(s) {
  if (!s) {
    fillText("#src-sha", "sha256: SUMMARY MISSING");
    return;
  }

  // Store the last rendered pack so UI controls (telemetry track switch) can re-render.
  try {
    window.__SIGMA_LAST_PACK = s;
  } catch (e) {
    // ignore
  }

  // Source links
  const src = s.source?.b_compare_json || s.source?.path || "#";
  const sha = s.source?.b_compare_sha256 || s.source?.sha256 || "UNKNOWN";
  const srcEl = document.getElementById("src-bcompare");
  if (srcEl) {
    srcEl.textContent = src;
    const isAbs = src.startsWith("http://") || src.startsWith("https://") || src.startsWith("file:");
    srcEl.href = src.startsWith("#") ? "#" : (isAbs ? src : "../" + src);
  }
  // Any inline "open artifact" links should follow the same source path (no hardcoded repo paths).
  document.querySelectorAll('a[data-artifact="b_compare"]').forEach((a) => {
    const isAbs = src.startsWith("http://") || src.startsWith("https://") || src.startsWith("file:");
    a.href = src.startsWith("#") ? "#" : (isAbs ? src : "../" + src);
  });
  fillText("#src-sha", sha === "UNKNOWN" ? "sha256: —" : ("sha256: " + String(sha).slice(0, 16) + "…"));

  // OOM boundary
  const n80 = s.analytic?.oom_wall?.n_at_h100_80gb;
  fillText("#oom-n80", n80 ? `N≈${n80.toLocaleString()} (≈80GB)` : "N≈UNKNOWN");

  // Data-driven fills (legacy paths)
  const nodes = document.querySelectorAll("[data-path]");
  nodes.forEach((el) => {
    const path = el.getAttribute("data-path");
    const val = getPath(s, path);
    let out = val;
    if (typeof val === "number") {
      if (path.endsWith("p95") || path.endsWith("p99") || path.endsWith("avg")) out = fmt(val, 3);
      else if (path.endsWith("joules_per_query")) out = fmt(val, 3);
      else if (path.endsWith("power_w_avg")) out = fmt(val, 1);
      else if (path.endsWith("gpu_util_pct_avg")) out = fmt(val, 1);
      else if (path.endsWith("qps")) out = fmt(val, 3);
      else out = String(val);
    } else if (val === undefined) out = "—";
    el.textContent = out;
  });

  // Gates: exactness
  const accB = _num(getPath(s, "metrics.baseline.top1_accuracy")) ?? _num(getPath(s, "measured.baseline_vector_scan.accuracy.top1_accuracy"));
  const accO = _num(getPath(s, "metrics.omega.top1_accuracy")) ?? _num(getPath(s, "measured.ctdr.accuracy.top1_accuracy"));
  const exactOk = accB !== null && accO !== null && accB >= 1.0 && accO >= 1.0;
  _setGate("gate-exactness", exactOk ? "pass" : "fail", exactOk ? "top‑1=1.0" : "top‑1 must be 1.0");

  // Gates: GPU util (min 70, target 85)
  const utilB = _num(getPath(s, "metrics.baseline.gpu_util_pct_avg")) ?? _num(getPath(s, "measured.baseline_vector_scan.energy.gpu_util_pct_avg"));
  const utilO = _num(getPath(s, "metrics.omega.gpu_util_pct_avg")) ?? _num(getPath(s, "measured.ctdr.energy.gpu_util_pct_avg"));
  if (utilB !== null) _setBar("bar-util-baseline", utilB);
  if (utilO !== null) _setBar("bar-util-omega", utilO);
  const utilOk = utilO !== null && utilO >= 70.0;
  _setGate("gate-util", utilOk ? "pass" : "fail", utilO !== null ? `${utilO.toFixed(1)}%` : "missing");

  // Gates: power stress (avg / limit)
  const pLimit = _num(getPath(s, "gpu.power_limit_w")) ?? 350.0;
  const pB = _num(getPath(s, "metrics.baseline.power_w_avg")) ?? _num(getPath(s, "measured.baseline_vector_scan.energy.power_w_avg"));
  const pO = _num(getPath(s, "metrics.omega.power_w_avg")) ?? _num(getPath(s, "measured.ctdr.energy.power_w_avg"));
  if (pB !== null) _setBar("bar-power-baseline", (pB / pLimit) * 100.0);
  if (pO !== null) _setBar("bar-power-omega", (pO / pLimit) * 100.0);
  const pOk = pO !== null && (pO / pLimit) <= 0.85;
  _setGate("gate-power", pOk ? "pass" : "warn", pO !== null ? `${pO.toFixed(0)}W / ${pLimit.toFixed(0)}W` : "missing");

  renderTelemetry(s);

  // Memoization/routing track gate (M<<N range scan vs full scan)
  const memo = getPath(s, "tracks.memoization_prefix_range.data");
  if (memo) {
    const ratio = _num(getPath(s, "tracks.memoization_prefix_range.data.delta.energy_per_query_ratio_full_over_range"));
    const minR = _num(getPath(s, "tracks.memoization_prefix_range.data.config.pass_criteria.min_energy_ratio")) ?? 100.0;
    const pass = (ratio !== null) && ratio >= minR;
    _setGate("gate-memo", pass ? "pass" : "fail", ratio !== null ? `${ratio.toFixed(1)}× (min ${minR.toFixed(0)}×)` : "missing");
  } else {
    _setGate("gate-memo", "warn", "missing track");
  }
}

async function _loadPackFromFile(file) {
  const txt = await file.text();
  return JSON.parse(txt);
}

function main() {
  renderSummary(window.SIGMA_PUBLIC_SUMMARY);
  renderTelemetry(window.SIGMA_PUBLIC_SUMMARY);

  const inp = document.getElementById("packFile");
  if (inp) {
    inp.addEventListener("change", async (ev) => {
      const f = ev.target.files && ev.target.files[0];
      if (!f) return;
      try {
        const j = await _loadPackFromFile(f);
        renderSummary(j);
      } catch (e) {
        fillText("#src-sha", "sha256: FAILED TO LOAD PACK");
      }
    });
  }

  const trackSel = document.getElementById("telemetryTrack");
  if (trackSel) {
    trackSel.addEventListener("change", () => {
      // Use the current rendered object (best-effort): reuse global if no user pack loaded.
      // renderSummary already calls renderTelemetry; we call explicitly so switching track updates immediately.
      renderTelemetry(window.__SIGMA_LAST_PACK || window.SIGMA_PUBLIC_SUMMARY);
    });
  }

  const exportBtn = document.getElementById("exportBtn");
  if (exportBtn) {
    exportBtn.addEventListener("click", () => {
      const data = window.__SIGMA_LAST_PACK || window.SIGMA_PUBLIC_SUMMARY;
      if (!data) return;
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `audit_receipt_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    });
  }
}

document.addEventListener("DOMContentLoaded", main);


