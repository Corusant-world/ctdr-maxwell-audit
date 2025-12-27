## Babel Challenge runner (public-safe)

Goal: a **procedural** “Library of Babel” style challenge (seed → dataset) that demonstrates:

- **Exactness** (verified correctness, not vibes)
- **Hierarchy** (structured keys / paths)
- **Memoization** (repeated queries → cache hits)
- **Scaling** (baseline cost grows with N; DHM/Omega aims for bounded-cost retrieval)

Hard rules:

- No CUDA kernel source / PTX / SASS / bindings.
- No Landauer / entropy marketing, no NFTs/blockchain.
- Only measured metrics + receipts + hashes.

### Run

From repo root:

```bash
python babel_challenge/run_babel_challenge.py --out-dir babel_challenge/out/latest
```

### GPU mode (H100)

On a Linux H100 box where `ctdr_python` is available, the runner will additionally emit `ctdr_dpx_*` results by calling:

- `ctdr_python.dpx_lcp_index_load(...)`
- `ctdr_python.dpx_lcp_index_set_query(...)`
- `ctdr_python.dpx_lcp_index_query_top1()`

If import fails, set:

```bash
export CTDR_PYTHON_PATH=/path/to/ctdr_python_build_or_wheel
```

For receipts:

```bash
python babel_challenge/run_babel_challenge.py \
  --out-dir babel_challenge/out/h100 \
  --n-docs 200000 --n-queries 20000 --repeat-pct 0.8 \
  --enable-energy-receipts --emit-nvidia-smi --sample-interval-s 0.1
```

Artifacts written into `--out-dir`:

- `scenario.json` (seed + parameters)
- `dataset_spec.json` (how the dataset is generated)
- `truth.json` (ground truth answers for the generated queries)
- `results.json` (accuracy + latency stats + QPS)
- `receipt_energy.json` (optional: NVML/nvidia-smi samples + Joules integration)
- `receipt_hashes.json` (sha256 hashes of artifacts)


