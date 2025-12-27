# CTDR: Maxwell Audit (v1.0)
> Solving the H100 NxN Materialization Wall.

## 1. THE FORENSIC EVIDENCE
The physical limit of 80GB HBM3 on H100. At scale (N=500k+), standard fp16 NxN materialization is impossible. 

![OOM Wall](https://raw.githubusercontent.com/Corusant-world/ctdr-maxwell-audit/main/assets/graph_oom_wall.png)

## 2. THE SOLUTION: CTDR (Cold Tensor Deterministic Reasoning)
- **90.4% SM Utilization** sustained.
- **70% Reduction** in energy per query (at scale).
- **Zero Hallucinations** via deterministic p-adic invariants.

![Energy Receipts](https://raw.githubusercontent.com/Corusant-world/ctdr-maxwell-audit/main/assets/graph_joules_per_query.png)

> **Note on Benchmarks:** In the baseline (small-N) comparison, CTDR carries a constant overhead for p-adic quantization and DPX-indexing. While energy use is comparable at low scale, the **asymmetry kicks in as N grows**: where vector scans scale linearly toward OOM, CTDR routing maintains flat energy costs.

## 3. QUICK START (30 Seconds)
Run the audit dashboard locally and compare your GPU receipts.

```bash
# 1. Clone
git clone https://github.com/Corusant-world/ctdr-maxwell-audit.git && cd ctdr-maxwell-audit

# 2. Launch Maxwell Dashboard
# (Windows)
start maxwell_dashboard/index.html
# (Mac)
open maxwell_dashboard/index.html
```

## 4. ACTION ITEMS
1. **Load Evidence**: Use the "Load a pack" button to import [evidence.zip](evidence_public/evidence.zip).
2. **Compare**: View the **"Memoization / routing track (M≪N)"** section in the dashboard to see 100x efficiency gains at scale.
3. **Audit**: Use "Export Audit Receipt" to verify results.

## 5. TECHNICAL INQUIRY & COLLABORATION
This release is a public-safe baseline intended to foster discussion on deterministic reasoning and GPU efficiency at scale. 

If you are an infrastructure owner (Inference/Retrieval/Perf) interested in a technical deep-dive into the CTDR/SIGMA stack or OOM wall mitigation strategies, I am open to a technical screen to discuss results and integration.

- **Lead Engineer:** [Stanislav Byriukov]
- **Focus:** Deterministic substrates, ultrametric memory, and high-density GPU orchestration.
