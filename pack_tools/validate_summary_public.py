#!/usr/bin/env python3
"""
Validate summary_public.json against Pack Standard v1.

No external deps (no jsonschema). This is a minimal structural validator.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]  # public_release_maxwell/
SCHEMA_FILE = REPO_ROOT / "pack_format" / "summary_public.schema.json"


def _load_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def _err(errors: List[str], msg: str) -> None:
    errors.append(msg)


def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate(summary: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    if not isinstance(summary, dict):
        return False, ["root must be an object"]

    if summary.get("schema") != "sigma_summary_public_v1":
        _err(errors, "schema must be 'sigma_summary_public_v1'")

    gpu = summary.get("gpu")
    if not isinstance(gpu, dict) or not isinstance(gpu.get("name"), str) or not gpu.get("name"):
        _err(errors, "gpu.name must be a non-empty string")

    metrics = summary.get("metrics")
    if not isinstance(metrics, dict):
        _err(errors, "metrics must be an object")
        return False, errors

    for block in ("omega", "baseline"):
        m = metrics.get(block)
        if not isinstance(m, dict):
            _err(errors, f"metrics.{block} must be an object")
            continue
        for k in ("qps", "lat_p95_ms", "top1_accuracy"):
            if k not in m:
                _err(errors, f"metrics.{block}.{k} missing")
                continue
            v = m.get(k)
            if v is not None and not _is_num(v):
                _err(errors, f"metrics.{block}.{k} must be number|null")
        acc = m.get("top1_accuracy")
        if acc is not None and _is_num(acc) and not (0.0 <= float(acc) <= 1.0):
            _err(errors, f"metrics.{block}.top1_accuracy out of range [0,1]")

    disc = summary.get("disclaimers")
    if not isinstance(disc, list) or not disc or not all(isinstance(x, str) for x in disc):
        _err(errors, "disclaimers must be a non-empty string array")

    # Optional telemetry: minimal structural checks (keep validator lightweight).
    tel = summary.get("telemetry")
    if tel is not None:
        if not isinstance(tel, dict):
            _err(errors, "telemetry must be an object if present")
        else:
            for block in ("omega", "baseline"):
                b = tel.get(block)
                if b is None:
                    continue
                if not isinstance(b, dict):
                    _err(errors, f"telemetry.{block} must be an object")
                    continue
                gpu = b.get("gpu")
                if gpu is None:
                    continue
                if not isinstance(gpu, dict):
                    _err(errors, f"telemetry.{block}.gpu must be an object")
                    continue
                t = gpu.get("t_s")
                pw = gpu.get("power_w")
                if t is not None and (not isinstance(t, list) or not all(_is_num(x) for x in t)):
                    _err(errors, f"telemetry.{block}.gpu.t_s must be a number array if present")
                if pw is not None and (not isinstance(pw, list) or not all(_is_num(x) for x in pw)):
                    _err(errors, f"telemetry.{block}.gpu.power_w must be a number array if present")
                if isinstance(t, list) and isinstance(pw, list) and len(t) != len(pw):
                    _err(errors, f"telemetry.{block}.gpu arrays must have matching lengths (t_s vs power_w)")

    return (len(errors) == 0), errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("summary_json", type=str, help="Path to summary_public.json")
    args = ap.parse_args()

    p = Path(args.summary_json)
    if not p.exists():
        print(f"FAIL: missing file: {p}")
        return 2

    s = _load_json(p)
    ok, errs = validate(s if isinstance(s, dict) else {})

    if ok:
        print("PASS: summary_public.json conforms to Pack Standard v1 (minimal checks).")
        if SCHEMA_FILE.exists():
            print(f"Schema reference: {SCHEMA_FILE}")
        return 0

    print("FAIL: summary_public.json invalid")
    for e in errs:
        print(f"- {e}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())


