"""
Public-safe asset generator (PNG) for the "3-link forcing package".

Hard constraints:
- No kernel source / PTX / SASS / bindings are read or emitted here.
- Charts must be reproducible from existing public-safe JSON artifacts.

Outputs:
- assets/graph_oom_wall.png
- assets/graph_joules_per_query.png
- assets/summary_public.json
- assets/summary_public.js
"""

from __future__ import annotations

import json
import math
import hashlib
from pathlib import Path
from typing import Any, Dict, Tuple

from PIL import Image, ImageDraw, ImageFont


REPO_ROOT = Path(__file__).resolve().parents[1]  # public_release_maxwell/
ASSETS_DIR = REPO_ROOT / "assets"

# Data source for measured J/query chart (already generated evidence).
DEFAULT_JQUERY_JSON = (
    ASSETS_DIR / "B_compare.json"
)


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def _sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _font(size: int) -> ImageFont.ImageFont:
    # Pillow's default bitmap font is always available. Keep it deterministic.
    return ImageFont.load_default()


def _draw_axes(
    draw: ImageDraw.ImageDraw,
    *,
    box: Tuple[int, int, int, int],
    title: str,
    x_label: str,
    y_label: str,
) -> None:
    x0, y0, x1, y1 = box
    # Frame
    draw.rectangle([x0, y0, x1, y1], outline=(0, 0, 0), width=2)
    # Title
    draw.text((x0, y0 - 18), title, fill=(0, 0, 0), font=_font(14))
    # Axis labels
    draw.text((x0, y1 + 6), x_label, fill=(0, 0, 0), font=_font(12))
    draw.text((x0 - 2, y0 - 30), y_label, fill=(0, 0, 0), font=_font(12))


def _oom_wall_plot(out_path: Path) -> None:
    """
    Plot: required HBM (GB) for explicit fp16 NxN materialization vs N.
    Uses an analytic formula: bytes = N^2 * 2.
    Visualized in log-log (by applying log10 transform to axes).
    """
    W, H = 1100, 650
    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    plot = (120, 110, 1040, 520)  # left, top, right, bottom
    _draw_axes(
        draw,
        box=plot,
        title="OOM wall (analytic): fp16 NxN materialization vs H100 80GB",
        x_label="Sequence length N (log scale)",
        y_label="HBM required (GB) (log scale)",
    )

    # Points (log-spaced) to plot.
    ns = [1_000, 2_000, 5_000, 10_000, 20_000, 50_000, 100_000, 200_000, 500_000, 1_000_000]
    # Use decimal GB for clarity: H100 is marketed as 80 GB.
    gb = [(n * n * 2) / 1_000_000_000 for n in ns]  # GB

    # Axis transform: log10 on both axes.
    x_vals = [math.log10(n) for n in ns]
    y_vals = [math.log10(max(v, 1e-9)) for v in gb]

    x_min, x_max = min(x_vals), max(x_vals)
    y_min, y_max = min(y_vals), max(y_vals)

    def x_map(x: float) -> int:
        x0, y0, x1, y1 = plot
        return int(x0 + (x - x_min) * (x1 - x0) / (x_max - x_min))

    def y_map(y: float) -> int:
        x0, y0, x1, y1 = plot
        return int(y1 - (y - y_min) * (y1 - y0) / (y_max - y_min))

    # Draw grid ticks for N.
    for n in [1_000, 10_000, 100_000, 1_000_000]:
        lx = math.log10(n)
        xx = x_map(lx)
        draw.line([(xx, plot[1]), (xx, plot[3])], fill=(235, 235, 235), width=1)
        draw.text((xx - 18, plot[3] + 20), f"{n//1000}k" if n < 1_000_000 else "1M", fill=(0, 0, 0), font=_font(12))

    # Draw grid ticks for GB.
    for g in [0.01, 0.1, 1, 10, 80, 100, 500, 1000]:
        ly = math.log10(g)
        if ly < y_min or ly > y_max:
            continue
        yy = y_map(ly)
        draw.line([(plot[0], yy), (plot[2], yy)], fill=(235, 235, 235), width=1)
        draw.text((plot[0] - 55, yy - 6), f"{g:g}", fill=(0, 0, 0), font=_font(12))

    # H100 80GB line (marketing / decimal).
    h100_gb = 80.0
    ly80 = math.log10(h100_gb)
    if y_min <= ly80 <= y_max:
        yy80 = y_map(ly80)
        draw.line([(plot[0], yy80), (plot[2], yy80)], fill=(220, 40, 40), width=3)
        draw.text((plot[0] + 8, yy80 - 18), "H100 80GB (HBM)", fill=(220, 40, 40), font=_font(12))

    # Plot curve.
    pts = [(x_map(x), y_map(y)) for x, y in zip(x_vals, y_vals)]
    draw.line(pts, fill=(20, 90, 200), width=4)
    for (x, y), n, g in zip(pts, ns, gb):
        r = 4
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(20, 90, 200))
        if n in (500_000,):
            draw.text((x + 10, y - 10), f"N=500k → {g:.0f} GB", fill=(0, 0, 0), font=_font(12))

    # Footer note: include "how many H100" at a couple points (dramatic, but purely analytic).
    # N=1M => 2TB => 25×80GB; N=2M => 8TB => 100×80GB (ignores overheads).
    draw.text(
        (120, 560),
        "Formula: fp16 NxN bytes = N^2 * 2 (decimal GB). N=1M → 2TB ≈ 25×H100(80GB); N=2M → 8TB ≈ 100×H100. (Memory only.)",
        fill=(0, 0, 0),
        font=_font(12),
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")


def _joules_per_query_plot(out_path: Path, *, src_json: Path) -> None:
    """
    Bar chart: measured J/query for CTDR vs vector_scan baseline, from B_compare.json.
    """
    d = _load_json(src_json)
    c = d["ctdr"]["energy"]["joules_per_query"]
    v = d["vector"]["energy"]["joules_per_query"]
    c_power = d["ctdr"]["energy"]["power_w_avg"]
    v_power = d["vector"]["energy"]["power_w_avg"]

    W, H = 1100, 650
    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    plot = (120, 120, 1040, 520)
    _draw_axes(
        draw,
        box=plot,
        title="Energy per query (measured, NVML) — CTDR vs vector_scan baseline",
        x_label="Method",
        y_label="J/query",
    )

    # y-scale with a bit of headroom
    y_max = max(float(c), float(v)) * 1.25
    y_min = 0.0

    def y_map(val: float) -> int:
        x0, y0, x1, y1 = plot
        return int(y1 - (val - y_min) * (y1 - y0) / (y_max - y_min))

    # Bars
    bar_w = 180
    gap = 180
    x_ctdr = plot[0] + 220
    x_vec = x_ctdr + bar_w + gap

    for x, val, color, label in [
        (x_ctdr, float(c), (20, 90, 200), "CTDR (DPX LCP index_top1_gpu)"),
        (x_vec, float(v), (120, 120, 120), "Vector baseline (GPU cosine fp32 scan)"),
    ]:
        y = y_map(val)
        draw.rectangle([x, y, x + bar_w, plot[3]], fill=color, outline=(0, 0, 0), width=2)
        draw.text((x, plot[3] + 20), label, fill=(0, 0, 0), font=_font(12))
        draw.text((x, y - 20), f"{val:.3f} J/query", fill=(0, 0, 0), font=_font(12))

    # Light y-grid
    for t in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]:
        if t > y_max:
            continue
        yy = y_map(t)
        draw.line([(plot[0], yy), (plot[2], yy)], fill=(235, 235, 235), width=1)
        draw.text((plot[0] - 55, yy - 6), f"{t:.1f}", fill=(0, 0, 0), font=_font(12))

    # Footer: power context + baseline caveat
    note = (
        f"Source: {src_json.relative_to(REPO_ROOT).as_posix()} | "
        f"Power avg: CTDR {c_power:.1f}W vs Vector {v_power:.1f}W | "
        "Baseline note: vector_scan is brute-force cosine over fp32 vectors (chunked), not semantic embeddings."
    )
    draw.text((120, 560), note, fill=(0, 0, 0), font=_font(12))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")

def _build_public_summary(*, src_json: Path) -> Dict[str, Any]:
    """
    Build a public-safe summary object used by the Maxwell dashboard.
    Hard rule: only derive from public-safe artifacts.
    """
    d = _load_json(src_json)

    # OOM wall analytic boundary: fp16 NxN bytes = N^2 * 2
    h100_gb = 80.0  # decimal GB
    n_at_80gb = int(math.isqrt(int(h100_gb * 1_000_000_000 / 2)))

    def _h100s_required_for_n(n: int) -> int:
        # Required GPUs just to fit fp16 NxN bytes, ignoring overheads.
        gb_req = (n * n * 2) / 1_000_000_000
        return int(math.ceil(gb_req / h100_gb))

    # Pack Standard v1 (community comparison) keys:
    # - keep legacy fields for the narrative dashboard
    # - add `schema` + `metrics` so compare.html can work with third-party packs
    ctdr = d.get("ctdr", {})
    vec = d.get("vector", {})

    summary: Dict[str, Any] = {
        "schema": "sigma_summary_public_v1",
        "source": {
            "b_compare_json": src_json.relative_to(REPO_ROOT).as_posix(),
            "b_compare_sha256": _sha256_hex(src_json),
        },
        "gpu": {
            "name": d.get("ctdr", {}).get("energy", {}).get("metadata", {}).get("name", "UNKNOWN"),
            "power_limit_w": d.get("ctdr", {}).get("energy", {}).get("metadata", {}).get("power_limit_w", None),
        },
        "metrics": {
            "omega": {
                "qps": float(ctdr.get("qps")) if ctdr.get("qps") is not None else None,
                "lat_p95_ms": float(ctdr.get("latency_ms", {}).get("p95")) if isinstance(ctdr.get("latency_ms"), dict) else None,
                "joules_per_query": float(ctdr.get("energy", {}).get("joules_per_query")) if isinstance(ctdr.get("energy"), dict) and ctdr.get("energy", {}).get("joules_per_query") is not None else None,
                "power_w_avg": float(ctdr.get("energy", {}).get("power_w_avg")) if isinstance(ctdr.get("energy"), dict) and ctdr.get("energy", {}).get("power_w_avg") is not None else None,
                "gpu_util_pct_avg": float(ctdr.get("energy", {}).get("gpu_util_pct_avg")) if isinstance(ctdr.get("energy"), dict) and ctdr.get("energy", {}).get("gpu_util_pct_avg") is not None else None,
                "temp_c_avg": float(ctdr.get("energy", {}).get("temp_c_avg")) if isinstance(ctdr.get("energy"), dict) and ctdr.get("energy", {}).get("temp_c_avg") is not None else None,
                "top1_accuracy": float(ctdr.get("accuracy", {}).get("top1_accuracy")) if isinstance(ctdr.get("accuracy"), dict) and ctdr.get("accuracy", {}).get("top1_accuracy") is not None else None,
            },
            "baseline": {
                "qps": float(vec.get("qps")) if vec.get("qps") is not None else None,
                "lat_p95_ms": float(vec.get("latency_ms", {}).get("p95")) if isinstance(vec.get("latency_ms"), dict) else None,
                "joules_per_query": float(vec.get("energy", {}).get("joules_per_query")) if isinstance(vec.get("energy"), dict) and vec.get("energy", {}).get("joules_per_query") is not None else None,
                "power_w_avg": float(vec.get("energy", {}).get("power_w_avg")) if isinstance(vec.get("energy"), dict) and vec.get("energy", {}).get("power_w_avg") is not None else None,
                "gpu_util_pct_avg": float(vec.get("energy", {}).get("gpu_util_pct_avg")) if isinstance(vec.get("energy"), dict) and vec.get("energy", {}).get("gpu_util_pct_avg") is not None else None,
                "temp_c_avg": float(vec.get("energy", {}).get("temp_c_avg")) if isinstance(vec.get("energy"), dict) and vec.get("energy", {}).get("temp_c_avg") is not None else None,
                "top1_accuracy": float(vec.get("accuracy", {}).get("top1_accuracy")) if isinstance(vec.get("accuracy"), dict) and vec.get("accuracy", {}).get("top1_accuracy") is not None else None,
            },
            "feasibility": {
                "oom_wall_n_at_80gb_fp16_nxn": n_at_80gb,
            },
        },
        "measured": {
            "ctdr": {
                "mode": d["ctdr"].get("mode"),
                "n_candidates": d["ctdr"].get("n_candidates"),
                "n_queries": d["ctdr"].get("n_queries"),
                "duration_s": d["ctdr"].get("duration_s"),
                "qps": d["ctdr"].get("qps"),
                "latency_ms": d["ctdr"].get("latency_ms"),
                "energy": d["ctdr"].get("energy"),
                "accuracy": d["ctdr"].get("accuracy"),
                "notes": d.get("notes", {}),
            },
            "baseline_vector_scan": {
                "mode": d["vector"].get("mode"),
                "n_candidates": d["vector"].get("n_candidates"),
                "n_queries": d["vector"].get("n_queries"),
                "duration_s": d["vector"].get("duration_s"),
                "qps": d["vector"].get("qps"),
                "latency_ms": d["vector"].get("latency_ms"),
                "energy": d["vector"].get("energy"),
                "accuracy": d["vector"].get("accuracy"),
                "notes": d.get("notes", {}),
            },
            "ratios": d.get("ratios", {}),
        },
        "analytic": {
            "oom_wall": {
                "formula": "fp16 NxN bytes = N^2 * 2",
                "h100_hbm_gb": h100_gb,
                "n_at_h100_80gb": n_at_80gb,
                "h100s_required_for_fp16_nxn": {
                    "n_200k": _h100s_required_for_n(200_000),
                    "n_500k": _h100s_required_for_n(500_000),
                    "n_1m": _h100s_required_for_n(1_000_000),
                    "n_2m": _h100s_required_for_n(2_000_000),
                },
                "example_points_gb": {
                    "n_200k": (200_000 * 200_000 * 2) / 1_000_000_000,
                    "n_500k": (500_000 * 500_000 * 2) / 1_000_000_000,
                    "n_1m": (1_000_000 * 1_000_000 * 2) / 1_000_000_000,
                },
            }
        },
        "assets": {
            "graph_oom_wall_png": "graph_oom_wall.png",
            "graph_joules_per_query_png": "graph_joules_per_query.png",
        },
        "disclaimers": [
            "Energy receipts shown here are measured (NVML) for one explicitly-defined baseline (see B_compare.json). Not a universal 'energy win' claim.",
            "Analytic OOM wall is a physical memory boundary (fp16 NxN bytes), not a benchmark dispute.",
            "No Landauer-limit marketing, and no blockchain/NFT claims: I use cryptographic hashes of receipts/artifacts instead.",
        ],
    }
    return summary

def _write_public_summary_assets(*, src_json: Path) -> None:
    summary = _build_public_summary(src_json=src_json)
    out_json = ASSETS_DIR / "summary_public.json"
    out_js = ASSETS_DIR / "summary_public.js"

    # Deterministic JSON (no timestamps), stable key order
    payload = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
    out_json.write_text(payload + "\n", encoding="utf-8")
    out_js.write_text(
        "/* Auto-generated. Do not edit. */\n"
        "window.SIGMA_PUBLIC_SUMMARY = "
        + payload
        + ";\n",
        encoding="utf-8",
    )


def main() -> int:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    oom_out = ASSETS_DIR / "graph_oom_wall.png"
    jq_out = ASSETS_DIR / "graph_joules_per_query.png"

    _oom_wall_plot(oom_out)
    _joules_per_query_plot(jq_out, src_json=DEFAULT_JQUERY_JSON)
    _write_public_summary_assets(src_json=DEFAULT_JQUERY_JSON)

    print(f"OK: wrote {oom_out}")
    print(f"OK: wrote {jq_out}")
    print(f"OK: wrote {ASSETS_DIR / 'summary_public.json'}")
    print(f"OK: wrote {ASSETS_DIR / 'summary_public.js'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


