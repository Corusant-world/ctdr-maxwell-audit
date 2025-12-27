# evidence.zip (public-safe) — what it contains and how to verify

This directory is used to build the **public-safe** evidence bundle for the “3-link forcing package”.

## What it is

`evidence.zip` is a **cheap-to-verify** artifact: **JSON/MD/LOG + 2 PNG graphs + nvidia-smi text snapshots**.

Hard rule: **no CUDA kernel source / PTX / SASS / bindings**.

## How to build (deterministic)

From this repo root:

```bash
python scripts/build_public_assets.py
python scripts/build_evidence_zip.py
```

Output:
- `assets/graph_oom_wall.png`
- `assets/graph_joules_per_query.png`
- `evidence_public/evidence.zip`

## What to look at first (inside the zip)

1) `README.md` (this file)
2) `assets/summary_public.json` — Pack Standard v1 (one pack; contains receipts + optional timeseries)
3) `assets/B_compare.json` — example AB artifact used by the dashboard (measured NVML fields)
4) `assets/memoization_prefix_range.json` — M≪N work-shrink track (energy canyon)
5) `pack_format/summary_public.schema.json` — Pack Standard v1 schema (community submissions)
6) `pack_tools/validate_summary_public.py` — validates a community `summary_public.json`
7) `maxwell_dashboard/index.html` — narrative dashboard (clickable)
8) `maxwell_dashboard/compare.html` — local “pack vs pack” comparator UI
9) `babel_challenge/run_babel_challenge.py` — procedural challenge runner (seed → dataset → results + hashes)

## Notes (avoid fake claims)

- The OOM wall chart is analytic (fp16 NxN bytes = \(N^2 \\times 2\)) and is meant to show a **physical memory boundary**, not a benchmark dispute.
- The J/query chart is taken from a **measured** NVML run (`B_compare.json`). Baseline is explicitly defined there.
- The Maxwell dashboard (static HTML) is included as a narrative layer; every number links back to an artifact.
- Community comparison uses Pack Standard v1: `summary_public.json` + hashes + receipts. Anyone can submit their own pack and compare in `compare.html`.


