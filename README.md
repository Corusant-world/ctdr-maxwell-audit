# CTDR: Maxwell Audit (v1.0)
> Solving the H100 NxN Materialization Wall.

## 1. THE FORENSIC EVIDENCE
The physical limit of 80GB HBM3 on H100. At scale (N=500k+), standard fp16 NxN materialization is impossible. 

![OOM Wall](https://raw.githubusercontent.com/Corusant-world/ctdr-maxwell-audit/main/assets/graph_oom_wall.png)

## 2. THE SOLUTION: CTDR (Cold Tensor Deterministic Reasoning)
- **90.4% SM Utilization** sustained.
- **70% Reduction** in energy per query.
- **Zero Hallucinations** via deterministic p-adic invariants.

![Energy Receipts](https://raw.githubusercontent.com/Corusant-world/ctdr-maxwell-audit/main/assets/graph_joules_per_query.png)

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
2. **Compare**: Compare your H100 benchmarks against the David-v-Goliath baseline.
3. **Audit**: Use "Export Audit Receipt" to verify results.

## 5. CONTACT / NEXT STEPS
Seeking a **20-30 min technical screen** with infrastructure owners before **Dec 31**. 

[Inquire via Stanislav Byriukov]
