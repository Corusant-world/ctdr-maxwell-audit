#!/usr/bin/env python3
"""
Babel Challenge runner (public-safe).

Key idea:
  - Generate a large, highly-colliding *hierarchical* keyspace procedurally from a seed (no downloads).
  - Run an exact retrieval workload with repeated queries (memoization opportunity).
  - Compare a baseline (naive LCP scan) vs DHM (Baire / p-adic tree + optional DPX GPU path).
  - Emit deterministic artifacts + receipt hashes.

Hard rules:
  - No kernel source / PTX / SASS / bindings are emitted.
  - No Landauer / entropy marketing, no NFTs/blockchain.
  - Only measurable metrics + receipts + hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def _sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def _nvidia_smi_snapshot() -> Tuple[bool, str]:
    """
    Best-effort nvidia-smi snapshot (works on GPU boxes, harmless elsewhere).
    Returns (ok, output_or_error).
    """
    try:
        r = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version,power.draw,utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu,clocks.sm",
                "--format=csv",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()
        if r.returncode != 0:
            return False, f"nvidia-smi failed (code={r.returncode}): {err or out}"
        return True, out
    except Exception as e:
        return False, f"nvidia-smi exception: {e}"


def _pct(samples: List[float], p: float) -> float:
    if not samples:
        return 0.0
    return float(np.percentile(np.asarray(samples, dtype=np.float64), p))


def _latency_stats_ms(lat_ms: List[float]) -> Dict[str, float]:
    if not lat_ms:
        return {"avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}
    a = np.asarray(lat_ms, dtype=np.float64)
    return {
        "avg": float(a.mean()),
        "p50": _pct(lat_ms, 50),
        "p95": _pct(lat_ms, 95),
        "p99": _pct(lat_ms, 99),
        "max": float(a.max()),
    }


def _lcp_len(a: str, b: str, *, max_len: int) -> int:
    n = min(len(a), len(b), max_len)
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def _naive_lcp_top1(query: str, candidates: List[str], *, max_len: int) -> Tuple[int, int]:
    """
    Baseline: scan all candidates and pick the max LCP. Returns (best_idx, best_lcp).
    Deterministic and exact, but scales with N.
    """
    best_idx = 0
    best_lcp = -1
    for i, s in enumerate(candidates):
        l = _lcp_len(query, s, max_len=max_len)
        if l > best_lcp:
            best_lcp = l
            best_idx = i
    return best_idx, int(best_lcp)


def _make_path(i: int, *, depth: int, fanout: int) -> str:
    """
    Procedural hierarchical key with high prefix collisions.
    """
    # Keep the prefix space small to create collisions (adversarial for approximate retrieval).
    parts = []
    x = i
    for d in range(depth - 1):
        parts.append(f"lvl{d}_{x % fanout:03d}")
        x //= fanout
    parts.append(f"doc_{i}")
    return " → ".join(parts)


def _make_edges(i: int, *, n_docs: int) -> Dict[str, int]:
    """
    Deterministic "cross references" to simulate interlinked documents.
    """
    # Two references per doc. This is not a semantics benchmark; it's a structured retrieval workload.
    return {
        "ref_a": int((i * 1315423911) % n_docs),
        "ref_b": int((i * 2654435761) % n_docs),
    }


@dataclass(frozen=True)
class QueryTask:
    qid: int
    doc_id: int
    query: str
    expect_path: str
    chain: Tuple[int, int, int]  # (doc_id, ref_a, ref_b)


def _build_dataset(*, seed: int, n_docs: int, depth: int, fanout: int) -> Tuple[List[str], List[Dict[str, Any]]]:
    # Deterministic: only depends on seed/n_docs/depth/fanout
    rng = np.random.RandomState(seed)
    order = np.arange(n_docs, dtype=np.int64)
    rng.shuffle(order)
    paths: List[str] = []
    contents: List[Dict[str, Any]] = []
    for idx, doc_id in enumerate(order.tolist()):
        p = _make_path(doc_id, depth=depth, fanout=fanout)
        paths.append(p)
        contents.append({"doc_id": int(doc_id), "edges": _make_edges(int(doc_id), n_docs=n_docs)})
    return paths, contents


def _build_queries(
    *,
    seed: int,
    n_queries: int,
    repeat_pct: float,
    paths: List[str],
    contents: List[Dict[str, Any]],
) -> List[QueryTask]:
    rng = np.random.RandomState(seed + 1)
    n_docs = len(paths)

    # Choose a small "hot set" to enable memoization.
    hot_k = max(1, int(max(1, n_docs) * max(0.0001, min(0.01, repeat_pct))))
    hot_ids = rng.choice(n_docs, size=hot_k, replace=False)

    tasks: List[QueryTask] = []
    for qid in range(n_queries):
        if rng.rand() < repeat_pct:
            idx = int(rng.choice(hot_ids))
        else:
            idx = int(rng.randint(0, n_docs))
        doc_id = int(contents[idx]["doc_id"])
        edges = contents[idx]["edges"]
        tasks.append(
            QueryTask(
                qid=qid,
                doc_id=doc_id,
                query=paths[idx],
                expect_path=paths[idx],
                chain=(doc_id, int(edges["ref_a"]), int(edges["ref_b"])),
            )
        )
    return tasks


def _try_import_dhm():
    import sys
    extra = os.environ.get("CTDR_PYTHON_PATH")
    if extra and extra not in sys.path:
        sys.path.insert(0, extra)
    from dhm import DynamicHierarchyManager  # type: ignore

    return DynamicHierarchyManager


def _try_import_ctdr_python() -> Optional[Any]:
    """
    Best-effort import of ctdr_python (DPX bindings).
    Uses CTDR_PYTHON_PATH if provided.
    """
    import sys

    extra = os.environ.get("CTDR_PYTHON_PATH")
    if extra and extra not in sys.path:
        sys.path.insert(0, extra)
    try:
        import ctdr_python  # type: ignore

        return ctdr_python
    except Exception:
        return None


def _encode_to_u16_padded(text: str, max_len: int) -> np.ndarray:
    """
    Encode text into uint16 array with padding to max_len.
    """
    out = np.zeros((max_len,), dtype=np.uint16)
    # Python loop is acceptable for moderate N; for very large N, generate directly in the GPU harness.
    n = min(len(text), max_len)
    for i in range(n):
        out[i] = np.uint16(ord(text[i]) & 0xFFFF)
    return out


def _encode_paths_u16(paths: List[str], max_len: int) -> np.ndarray:
    """
    Encode many paths into a contiguous (N, L) uint16 array.
    """
    n = len(paths)
    L = int(max_len)
    mat = np.zeros((n, L), dtype=np.uint16)
    for i, p in enumerate(paths):
        n_chars = min(len(p), L)
        for j in range(n_chars):
            mat[i, j] = np.uint16(ord(p[j]) & 0xFFFF)
    return np.ascontiguousarray(mat)


def _measure_method(
    *,
    name: str,
    tasks: List[QueryTask],
    get_top1_fn,
    memoize: bool,
) -> Dict[str, Any]:
    lat_ms: List[float] = []
    top1_correct = 0
    chain_correct = 0
    cache: Dict[str, Tuple[str, Any, float]] = {}
    cache_hits = 0
    cache_misses = 0

    t0 = time.perf_counter()
    for t in tasks:
        start = time.perf_counter()
        if memoize:
            cached = cache.get(t.query)
            if cached is not None:
                res = cached
                cache_hits += 1
            else:
                res = get_top1_fn(t.query)
                cache[t.query] = res
                cache_misses += 1
        else:
            res = get_top1_fn(t.query)

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        lat_ms.append(float(elapsed_ms))

        path = res[0] if res else None
        if path == t.expect_path:
            top1_correct += 1

        # "Context mapping" proxy: verify the doc's two references are consistent with the dataset
        # (This is still structured retrieval; it's not a semantics/LLM benchmark.)
        if res and isinstance(res[1], dict) and "edges" in res[1]:
            edges = res[1]["edges"]
            if (t.chain[1] == int(edges["ref_a"])) and (t.chain[2] == int(edges["ref_b"])):
                chain_correct += 1

    duration_s = time.perf_counter() - t0
    n = len(tasks)
    qps = (n / duration_s) if duration_s > 0 else 0.0

    return {
        "name": name,
        "n_queries": n,
        "duration_s": float(duration_s),
        "qps": float(qps),
        "latency_ms": _latency_stats_ms(lat_ms),
        "accuracy": {
            "top1_correct": int(top1_correct),
            "top1_accuracy": float(top1_correct / n) if n else 0.0,
            "chain_correct": int(chain_correct),
            "chain_accuracy": float(chain_correct / n) if n else 0.0,
        },
        "memoization": {
            "enabled": bool(memoize),
            "cache_hits": int(cache_hits),
            "cache_misses": int(cache_misses),
            "cache_size": int(len(cache)),
            "cache_hit_rate": float(cache_hits / max(1, (cache_hits + cache_misses))) if memoize else 0.0,
        },
    }


def _maybe_energy_receipt(
    *,
    out_dir: Path,
    gpu_id: int,
    sample_interval_s: float,
    workload_fn,
) -> Dict[str, Any]:
    """
    Best-effort receipts:
      - NVML sampling if available, else nvidia-smi polling, else "unavailable".
    """
    try:
        # Public bundle should be self-contained: prefer local energy_sampling.py.
        from energy_sampling import EnergySampler, integrate_energy_j, samples_to_timeseries  # type: ignore
    except Exception:
        # In monorepo runs, we may still have the internal module available.
        try:
            from integrations.benchmarks_scale.energy_sampling import EnergySampler, integrate_energy_j, samples_to_timeseries  # type: ignore
        except Exception as e:
            return {"backend": "unavailable", "error": f"import_failed: {e}"}

    sampler = EnergySampler(gpu_id=gpu_id, sample_interval_s=sample_interval_s)
    sampler.start()
    t0 = time.perf_counter()
    try:
        workload_fn()
    finally:
        duration_s = time.perf_counter() - t0
        sampler.stop()

    energy_j = integrate_energy_j(sampler.samples, duration_s=float(duration_s))
    # Simple aggregates (avoid huge dumps)
    p = [s.power_w for s in sampler.samples if s.power_w is not None]
    gpu_u = [s.gpu_util_pct for s in sampler.samples if s.gpu_util_pct is not None]
    temp = [s.temp_c for s in sampler.samples if s.temp_c is not None]
    mem_used = [s.mem_used_mb for s in sampler.samples if s.mem_used_mb is not None]

    receipt = {
        "backend": sampler.backend,
        "duration_s": float(duration_s),
        "samples": int(len(sampler.samples)),
        "energy_j": float(energy_j) if energy_j is not None else None,
        "power_w_avg": float(np.mean(p)) if p else None,
        "power_w_max": float(np.max(p)) if p else None,
        "gpu_util_pct_avg": float(np.mean(gpu_u)) if gpu_u else None,
        "gpu_util_pct_max": float(np.max(gpu_u)) if gpu_u else None,
        "temp_c_avg": float(np.mean(temp)) if temp else None,
        "temp_c_max": float(np.max(temp)) if temp else None,
        "mem_used_mb_avg": float(np.mean(mem_used)) if mem_used else None,
        "mem_used_mb_max": float(np.max(mem_used)) if mem_used else None,
        "metadata": sampler.metadata,
        "timeseries": samples_to_timeseries(sampler.samples, max_points=1200),
    }
    _write_json(out_dir / "receipt_energy.json", receipt)
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True, help="Output directory for artifacts")
    ap.add_argument("--seed", type=int, default=123, help="Dataset seed (deterministic)")
    ap.add_argument("--n-docs", type=int, default=200_000, help="Number of documents/keys to generate")
    ap.add_argument("--n-queries", type=int, default=20_000, help="Number of query tasks")
    ap.add_argument("--repeat-pct", type=float, default=0.8, help="Fraction of queries drawn from a hot set (0..1)")
    ap.add_argument("--depth", type=int, default=5, help="Hierarchy depth (path segments)")
    ap.add_argument("--fanout", type=int, default=256, help="Per-level fanout for collisions")
    ap.add_argument("--max-path-len", type=int, default=128, help="Max chars for LCP (baseline)")
    ap.add_argument("--enable-energy-receipts", action="store_true", help="Collect NVML/nvidia-smi receipts (best effort)")
    ap.add_argument("--emit-nvidia-smi", action="store_true", help="Write nvidia-smi before/after snapshots (best effort)")
    ap.add_argument("--gpu-id", type=int, default=0, help="GPU id for receipts (if enabled)")
    ap.add_argument("--sample-interval-s", type=float, default=0.1, help="Energy sample interval")
    ap.add_argument(
        "--force-dhm-cpu",
        action="store_true",
        help="Also run DHM on CPU fallback (can be slow; DHM is optimized for DPX GPU path).",
    )
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Scenario/spec
    scenario = {
        "seed": int(args.seed),
        "n_docs": int(args.n_docs),
        "n_queries": int(args.n_queries),
        "repeat_pct": float(args.repeat_pct),
        "depth": int(args.depth),
        "fanout": int(args.fanout),
        "max_path_len": int(args.max_path_len),
        "notes": [
            "Dataset is procedural (seed → paths + deterministic cross references). No downloads required.",
            "This is structured retrieval (exactness + hierarchy + memoization), not an LLM benchmark.",
        ],
    }
    dataset_spec = {
        "generator": "procedural_babel_v0",
        "path_format": "lvl{d}_{bucket:03d} → ... → doc_{i}",
        "edges": "2 deterministic cross refs per doc: ref_a, ref_b",
        "adversarial_property": "high prefix collisions to stress approximate retrieval",
    }

    _write_json(out_dir / "scenario.json", scenario)
    _write_json(out_dir / "dataset_spec.json", dataset_spec)

    env = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "ctdr_python_path_env": os.environ.get("CTDR_PYTHON_PATH"),
    }
    _write_json(out_dir / "environment.json", env)

    # Build dataset (in-memory index is unavoidable for retrieval; the key benefit here is 'no download')
    t_build0 = time.perf_counter()
    paths, contents = _build_dataset(seed=args.seed, n_docs=args.n_docs, depth=args.depth, fanout=args.fanout)
    build_s = time.perf_counter() - t_build0

    # Queries + truth
    tasks = _build_queries(seed=args.seed, n_queries=args.n_queries, repeat_pct=args.repeat_pct, paths=paths, contents=contents)
    truth = {
        "n_queries": int(len(tasks)),
        "answers": [
            {"qid": t.qid, "expect_path": t.expect_path, "chain": {"doc": t.chain[0], "ref_a": t.chain[1], "ref_b": t.chain[2]}}
            for t in tasks
        ],
    }
    _write_json(out_dir / "truth.json", truth)

    # Prepare DHM
    DynamicHierarchyManager = _try_import_dhm()
    dhm = DynamicHierarchyManager(use_gpu=True)
    for p, c in zip(paths, contents):
        dhm.insert(concept=p, content=c, path=p)

    dhm_stats = dhm.get_stats()
    gpu_available = bool(dhm_stats.get("gpu_available"))

    ctdr = _try_import_ctdr_python()
    ctdr_available = ctdr is not None and hasattr(ctdr, "dpx_lcp_index_load")

    # Exact index (O(1) lookup) — demonstrates "indexed retrieval avoids scan" without any GPU.
    exact_index = {p: c for p, c in zip(paths, contents)}

    # Baseline top1
    def baseline_top1(q: str):
        idx, _lcp = _naive_lcp_top1(q, paths, max_len=int(args.max_path_len))
        return (paths[idx], contents[idx], 0.0)

    def exact_index_top1(q: str):
        c = exact_index.get(q)
        if c is None:
            return ("", {}, 0.0)
        return (q, c, 1.0)

    # DHM top1 (use fast top1 when possible)
    def dhm_top1(q: str):
        r = dhm.search_top1(q)
        if r is None:
            return ("", {}, 0.0)
        return r

    # Direct DPX path (ctdr_python) — this is the "GPU story" when available.
    ctdr_candidates_u16: Optional[np.ndarray] = None
    ctdr_loaded = False

    def _ctdr_load_once() -> None:
        nonlocal ctdr_candidates_u16, ctdr_loaded
        if not ctdr_available or ctdr_loaded:
            return
        ctdr_candidates_u16 = _encode_paths_u16(paths, max_len=int(args.max_path_len))
        ok = bool(ctdr.dpx_lcp_index_load(ctdr_candidates_u16.tobytes(order="C"), int(ctdr_candidates_u16.shape[0])))
        if not ok:
            raise RuntimeError("ctdr_python.dpx_lcp_index_load returned false")
        # Warmup (one query)
        q0 = _encode_to_u16_padded(tasks[0].query, max_len=int(args.max_path_len))
        ok2 = bool(ctdr.dpx_lcp_index_set_query(q0.tobytes(order="C")))
        if not ok2:
            raise RuntimeError("ctdr_python.dpx_lcp_index_set_query returned false")
        _ = ctdr.dpx_lcp_index_query_top1()
        ctdr_loaded = True

    def ctdr_top1(q: str):
        _ctdr_load_once()
        q_u16 = _encode_to_u16_padded(q, max_len=int(args.max_path_len))
        ok2 = bool(ctdr.dpx_lcp_index_set_query(q_u16.tobytes(order="C")))
        if not ok2:
            raise RuntimeError("ctdr_python.dpx_lcp_index_set_query returned false")
        best_idx, _best_lcp = ctdr.dpx_lcp_index_query_top1()
        idx = int(best_idx)
        return (paths[idx], contents[idx], 1.0 if paths[idx] == q else 0.0)

    results: Dict[str, Any] = {
        "build": {"dataset_build_s": float(build_s), "dhm_stats": dhm_stats},
        "methods": {},
    }

    # Measure without memoization
    results["methods"]["baseline_no_memo"] = _measure_method(name="baseline_naive_lcp_scan", tasks=tasks, get_top1_fn=baseline_top1, memoize=False)
    results["methods"]["indexed_no_memo"] = _measure_method(name="indexed_exact_lookup", tasks=tasks, get_top1_fn=exact_index_top1, memoize=False)
    if gpu_available or args.force_dhm_cpu:
        results["methods"]["dhm_no_memo"] = _measure_method(name="dhm_baire_top1", tasks=tasks, get_top1_fn=dhm_top1, memoize=False)
    else:
        results["methods"]["dhm_no_memo"] = {"name": "dhm_baire_top1", "skipped": True, "reason": "gpu_not_available (use --force-dhm-cpu to measure CPU fallback)"}
    if ctdr_available:
        try:
            results["methods"]["ctdr_dpx_no_memo"] = _measure_method(name="ctdr_dpx_lcp_top1", tasks=tasks, get_top1_fn=ctdr_top1, memoize=False)
        except Exception as e:
            results["methods"]["ctdr_dpx_no_memo"] = {"name": "ctdr_dpx_lcp_top1", "error": str(e)}
    else:
        results["methods"]["ctdr_dpx_no_memo"] = {"name": "ctdr_dpx_lcp_top1", "skipped": True, "reason": "ctdr_python_not_available (set CTDR_PYTHON_PATH on H100 Linux box)"}

    # Measure with memoization (application-level cache)
    results["methods"]["baseline_memo"] = _measure_method(name="baseline_naive_lcp_scan", tasks=tasks, get_top1_fn=baseline_top1, memoize=True)
    results["methods"]["indexed_memo"] = _measure_method(name="indexed_exact_lookup", tasks=tasks, get_top1_fn=exact_index_top1, memoize=True)
    if gpu_available or args.force_dhm_cpu:
        results["methods"]["dhm_memo"] = _measure_method(name="dhm_baire_top1", tasks=tasks, get_top1_fn=dhm_top1, memoize=True)
    else:
        results["methods"]["dhm_memo"] = {"name": "dhm_baire_top1", "skipped": True, "reason": "gpu_not_available (use --force-dhm-cpu to measure CPU fallback)"}
    if ctdr_available:
        try:
            results["methods"]["ctdr_dpx_memo"] = _measure_method(name="ctdr_dpx_lcp_top1", tasks=tasks, get_top1_fn=ctdr_top1, memoize=True)
        except Exception as e:
            results["methods"]["ctdr_dpx_memo"] = {"name": "ctdr_dpx_lcp_top1", "error": str(e)}
    else:
        results["methods"]["ctdr_dpx_memo"] = {"name": "ctdr_dpx_lcp_top1", "skipped": True, "reason": "ctdr_python_not_available (set CTDR_PYTHON_PATH on H100 Linux box)"}

    # Optional receipts: measure only one representative workload (dhm_no_memo) to keep it short.
    if args.enable_energy_receipts:
        if args.emit_nvidia_smi:
            ok, txt = _nvidia_smi_snapshot()
            _write_text(out_dir / "nvidia_smi_before.txt", txt if txt else ("OK" if ok else ""))

        def _work():
            # Prefer DHM if GPU is available; otherwise measure the indexed lookup path (still meaningful receipts).
            if ctdr_available:
                _ = _measure_method(name="ctdr_dpx_lcp_top1", tasks=tasks[: min(5000, len(tasks))], get_top1_fn=ctdr_top1, memoize=False)
            elif gpu_available:
                _ = _measure_method(name="dhm_baire_top1", tasks=tasks[: min(5000, len(tasks))], get_top1_fn=dhm_top1, memoize=False)
            else:
                _ = _measure_method(name="indexed_exact_lookup", tasks=tasks[: min(5000, len(tasks))], get_top1_fn=exact_index_top1, memoize=False)

        receipt = _maybe_energy_receipt(
            out_dir=out_dir,
            gpu_id=int(args.gpu_id),
            sample_interval_s=float(args.sample_interval_s),
            workload_fn=_work,
        )
        results["receipt_energy"] = receipt

        if args.emit_nvidia_smi:
            ok, txt = _nvidia_smi_snapshot()
            _write_text(out_dir / "nvidia_smi_after.txt", txt if txt else ("OK" if ok else ""))
    else:
        if args.emit_nvidia_smi:
            ok, txt = _nvidia_smi_snapshot()
            _write_text(out_dir / "nvidia_smi_snapshot.txt", txt if txt else ("OK" if ok else ""))

    _write_json(out_dir / "results.json", results)

    # Receipt hashes (cheap-to-verify)
    hashes = {
        "scenario.json": _sha256_hex(out_dir / "scenario.json"),
        "dataset_spec.json": _sha256_hex(out_dir / "dataset_spec.json"),
        "environment.json": _sha256_hex(out_dir / "environment.json"),
        "truth.json": _sha256_hex(out_dir / "truth.json"),
        "results.json": _sha256_hex(out_dir / "results.json"),
    }
    if (out_dir / "receipt_energy.json").exists():
        hashes["receipt_energy.json"] = _sha256_hex(out_dir / "receipt_energy.json")
    if (out_dir / "nvidia_smi_before.txt").exists():
        hashes["nvidia_smi_before.txt"] = _sha256_hex(out_dir / "nvidia_smi_before.txt")
    if (out_dir / "nvidia_smi_after.txt").exists():
        hashes["nvidia_smi_after.txt"] = _sha256_hex(out_dir / "nvidia_smi_after.txt")
    if (out_dir / "nvidia_smi_snapshot.txt").exists():
        hashes["nvidia_smi_snapshot.txt"] = _sha256_hex(out_dir / "nvidia_smi_snapshot.txt")
    _write_json(out_dir / "receipt_hashes.json", hashes)

    print(f"OK: wrote artifacts to {out_dir}")
    print(f"Dataset build: {build_s:.2f}s | docs={len(paths)} | queries={len(tasks)}")
    print("DHM:", dhm_stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


