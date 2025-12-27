# CTDR: Maxwell Audit & Forensic Tool (v1.0)
**Public-safe evidence packet for H100 long-context compute.**

![OOM Wall](assets/graph_oom_wall.png)

## 1. THE PROBLEM: The NxN Materialization Wall
Current long-context benchmarks often ignore the physical limit of HBM. 
- At **N=500,000**, fp16 NxN materialization requires **~500 GB** of HBM.
- Result: **OOM (Out of Memory)** on a single 80GB H100.
- Strategy: If you can't stay operational when NxN is impossible, you don't own the scale.

## 2. QUICK START: Run the Audit
Clone this repo and open the **Maxwell Dashboard** locally to verify the evidence.

```bash
git clone https://github.com/Corusant-world/ctdr-maxwell-audit.git
cd ctdr-maxwell-audit
# Open the dashboard in your browser
open maxwell_dashboard/index.html
```

## 3. ACTIONABLE AUDIT: How to Test
1. **Download Evidence**: Get the [evidence.zip](evidence_public/evidence.zip) containing real NVML receipts.
2. **Launch Dashboard**: Open `maxwell_dashboard/index.html`.
3. **Compare Your GPU**: 
   - Run your own inference on H100.
   - Capture `nvidia-smi` telemetry.
   - Upload your `summary_public.json` to the dashboard via the **"Load a pack"** button.
   - Use **"Export Audit Receipt"** to save and share the comparison.

## 4. KEY METRICS (Verified)
- **SM Utilization:** 90.4% (Target: >85%)
- **Energy Efficiency:** Measured in Joules per Verified Query (J/VQ).
- **Feasibility:** Zero NxN materialization.

![Energy Receipts](assets/graph_joules_per_query.png)

## 5. THE ASK
Seeking a **20-30 min technical screen** with infrastructure owners (Inference/Retrieval/Perf) before **Dec 31**. 

**Dec 31 is the hard cut-off.** After this, we proceed with selected partners for the full SDK integration.

---
**Organization:** [Corusant World]
**Lead Engineer:** Stanislav Byriukov
**Status:** Public-safe release. No kernel source/PTX included.
