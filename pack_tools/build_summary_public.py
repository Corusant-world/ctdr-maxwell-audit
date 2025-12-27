#!/usr/bin/env python3
"""
Build a Pack Standard v1 summary_public.json from public-safe artifacts.

Supported inputs:
  - AB compare JSON (B_compare.json) used by the CTDR public teaser.
  - Babel challenge out-dir (results.json + receipt_energy.json optionally).

No external deps.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional


def _load_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def _sha256_hex(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _get(d: Dict[str, Any], path: str) -> Any:
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _num(x: Any) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    return None


def _repo_root() -> Path:
    # public_release_maxwell/
    return Path(__file__).resolve().parents[1]


def _maybe_attach_memoization_track(summary: Dict[str, Any]) -> None:
    """
    Attach a public-safe "memoization/routing" track if the artifact exists.

    This track is intentionally separate from the AB compare track, because it demonstrates
    the asymmetry when work shrinks from N to M<<N (e.g., prefix-bucket routing with range top-1).

    Source artifact (public-safe):
      assets/memoization_prefix_range.json
    """
    p = _repo_root() / "assets" / "memoization_prefix_range.json"
    if not p.exists():
        return
    try:
        d = _load_json(p)
        if not isinstance(d, dict):
            return
    except Exception:
        return

    tracks = summary.setdefault("tracks", {})
    tracks["memoization_prefix_range"] = {
        "schema": "sigma_track_memoization_prefix_range_v1",
        "source": {"type": "artifact_json", "path": str(p.relative_to(_repo_root()).as_posix()), "sha256": _sha256_hex(p)},
        "data": d,
    }

    # Add a short disclaimer line if not already present.
    disc = summary.get("disclaimers")
    if isinstance(disc, list):
        msg = "Memoization/routing track reports an M<<N work-shrink (range top-1 on bucketed layout). It's a different axis than vector_scan AB."
        if msg not in disc:
            disc.append(msg)


def build_from_ab_compare(b_compare: Dict[str, Any], *, source_path: str, source_sha: str) -> Dict[str, Any]:
    c = b_compare.get("ctdr", {})
    v = b_compare.get("vector", {})

    summary: Dict[str, Any] = {
        "schema": "sigma_summary_public_v1",
        "gpu": {
            "name": _get(c, "energy.metadata.name") or _get(v, "energy.metadata.name") or "UNKNOWN",
            "power_limit_w": _num(_get(c, "energy.metadata.power_limit_w") or _get(v, "energy.metadata.power_limit_w")),
        },
        "metrics": {
            "omega": {
                "qps": _num(_get(c, "qps")),
                "lat_p95_ms": _num(_get(c, "latency_ms.p95")),
                "joules_per_query": _num(_get(c, "energy.joules_per_query")),
                "power_w_avg": _num(_get(c, "energy.power_w_avg")),
                "gpu_util_pct_avg": _num(_get(c, "energy.gpu_util_pct_avg")),
                "temp_c_avg": _num(_get(c, "energy.temp_c_avg")),
                "top1_accuracy": _num(_get(c, "accuracy.top1_accuracy")),
            },
            "baseline": {
                "qps": _num(_get(v, "qps")),
                "lat_p95_ms": _num(_get(v, "latency_ms.p95")),
                "joules_per_query": _num(_get(v, "energy.joules_per_query")),
                "power_w_avg": _num(_get(v, "energy.power_w_avg")),
                "gpu_util_pct_avg": _num(_get(v, "energy.gpu_util_pct_avg")),
                "temp_c_avg": _num(_get(v, "energy.temp_c_avg")),
                "top1_accuracy": _num(_get(v, "accuracy.top1_accuracy")),
            },
            "feasibility": {
                # fp16 NxN bytes = N^2*2 => 80GB boundary at ~200k
                "oom_wall_n_at_80gb_fp16_nxn": 200000,
            },
        },
        "source": {
            "type": "ab_compare",
            "path": source_path,
            "sha256": source_sha,
            "baseline_note": _get(b_compare, "notes.baseline"),
            "truth_mode": _get(b_compare, "notes.truth_mode"),
        },
        "disclaimers": [
            "Energy receipts are measured (NVML/nvidia-smi) for one explicitly-defined baseline. Not a universal 'energy win' claim.",
            "OOM wall is an analytic physical memory boundary (fp16 NxN bytes), not a benchmark dispute.",
            "No Landauer-limit marketing, and no blockchain/NFT claims: I publish cryptographic hashes of receipts/artifacts instead.",
        ],
    }

    _maybe_attach_memoization_track(summary)
    return summary


def _maybe_attach_energy_timeseries(summary: Dict[str, Any], *, block: str, energy_obj: Any) -> None:
    """
    Attach downsampled time-series telemetry to the summary if present.

    Expected shape:
      energy_obj["timeseries"] = { "t_s": [...], "power_w": [...], ... }
    """
    if not isinstance(energy_obj, dict):
        return
    ts = energy_obj.get("timeseries")
    if not isinstance(ts, dict):
        return
    if not isinstance(ts.get("t_s"), list) or not isinstance(ts.get("power_w"), list):
        return
    tel = summary.setdefault("telemetry", {})
    b = tel.setdefault(block, {})
    b["gpu"] = ts


def build_from_babel_out(results: Dict[str, Any], receipt_energy: Optional[Dict[str, Any]], *, source_path: str) -> Dict[str, Any]:
    # Prefer ctdr_dpx if present, else indexed baseline numbers (babel can run without GPU).
    methods = results.get("methods", {}) if isinstance(results, dict) else {}
    omega = methods.get("ctdr_dpx_no_memo") or methods.get("indexed_no_memo") or {}
    baseline = methods.get("baseline_no_memo") or {}

    gpu_name = None
    if receipt_energy and isinstance(receipt_energy, dict):
        md = receipt_energy.get("metadata") or {}
        if isinstance(md, dict) and md.get("name"):
            gpu_name = str(md.get("name"))

    summary: Dict[str, Any] = {
        "schema": "sigma_summary_public_v1",
        "gpu": {
            "name": gpu_name or "UNKNOWN",
            "power_limit_w": _num(_get(receipt_energy or {}, "metadata.power_limit_w")),
        },
        "metrics": {
            "omega": {
                "qps": _num(_get(omega, "qps")),
                "lat_p95_ms": _num(_get(omega, "latency_ms.p95")),
                "joules_per_query": None,
                "power_w_avg": _num(_get(receipt_energy or {}, "power_w_avg")),
                "gpu_util_pct_avg": _num(_get(receipt_energy or {}, "gpu_util_pct_avg")),
                "temp_c_avg": _num(_get(receipt_energy or {}, "temp_c_avg")),
                "top1_accuracy": _num(_get(omega, "accuracy.top1_accuracy")),
            },
            "baseline": {
                "qps": _num(_get(baseline, "qps")),
                "lat_p95_ms": _num(_get(baseline, "latency_ms.p95")),
                "joules_per_query": None,
                "power_w_avg": None,
                "gpu_util_pct_avg": None,
                "temp_c_avg": None,
                "top1_accuracy": _num(_get(baseline, "accuracy.top1_accuracy")),
            },
        },
        "source": {
            "type": "babel_challenge",
            "path": source_path,
            "note": "Babel summary is derived from results.json; energy receipts (if present) are reported separately.",
        },
        "disclaimers": [
            "Babel Challenge is structured retrieval (exactness + hierarchy + memoization), not an LLM semantics benchmark.",
            "Energy receipts are optional; include receipt_energy.json for power/util/temp/J integration.",
            "No Landauer-limit marketing, and no blockchain/NFT claims: I publish cryptographic hashes of receipts/artifacts instead.",
        ],
    }

    # If receipt includes integrated energy, compute J/query using omega's query count if available.
    if receipt_energy and isinstance(receipt_energy, dict):
        energy_j = _num(receipt_energy.get("energy_j"))
        dur_s = _num(receipt_energy.get("duration_s"))
        # For Babel, omega.n_queries is available in results
        n_q = _num(_get(omega, "n_queries"))
        if energy_j is not None and n_q is not None and n_q > 0:
            summary["metrics"]["omega"]["joules_per_query"] = float(energy_j / n_q)

        _maybe_attach_energy_timeseries(summary, block="omega", energy_obj=receipt_energy)

    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="Output path for summary_public.json")
    ap.add_argument("--ab-compare", help="Path to B_compare.json")
    ap.add_argument("--babel-out", help="Path to Babel out-dir (contains results.json, optional receipt_energy.json)")
    args = ap.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.ab_compare and args.babel_out:
        raise SystemExit("Pick only one input: --ab-compare OR --babel-out")
    if not args.ab_compare and not args.babel_out:
        raise SystemExit("Missing input: use --ab-compare or --babel-out")

    if args.ab_compare:
        p = Path(args.ab_compare)
        d = _load_json(p)
        summary = build_from_ab_compare(d, source_path=str(p.as_posix()), source_sha=_sha256_hex(p))

        # Optional: if sibling per-engine JSONs exist and include energy.timeseries, attach them.
        # (This is best-effort because packs can be built from a standalone B_compare.json.)
        try:
            base = p.parent
            ctdr_p = base / "B_ctdr.json"
            vec_p = base / "B_vector_flat.json"
            if ctdr_p.exists():
                ctdr_d = _load_json(ctdr_p)
                if isinstance(ctdr_d, dict):
                    _maybe_attach_energy_timeseries(summary, block="omega", energy_obj=_get(ctdr_d, "energy") or {})
            if vec_p.exists():
                vec_d = _load_json(vec_p)
                if isinstance(vec_d, dict):
                    _maybe_attach_energy_timeseries(summary, block="baseline", energy_obj=_get(vec_d, "energy") or {})
        except Exception:
            pass
    else:
        ddir = Path(args.babel_out)
        results_p = ddir / "results.json"
        if not results_p.exists():
            raise SystemExit(f"Missing {results_p}")
        results = _load_json(results_p)
        receipt_p = ddir / "receipt_energy.json"
        receipt = _load_json(receipt_p) if receipt_p.exists() else None
        summary = build_from_babel_out(results, receipt, source_path=str(ddir.as_posix()))

    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"OK: wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


