# Maxwell: GPU Logic Forensic & OOM Wall Finder (v1.0)
> **"Where does your H100 actually break?"** — A zero-config utility to audit memory boundaries and logic stability in high-density inference.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![GPU: H100/Blackwell](https://img.shields.io/badge/Hardware-H100%20%7C%20Blackwell-orange.svg)](#)

---

## 1. The Core Concept
Maxwell treats **autonomy as a physical constraint problem**. 

Most long-context benchmarks ignore the **NxN Materialization Wall**. This tool provides the forensic evidence and the mathematical substrate (CTDR) to stay operational when standard fp16 NxN materialization becomes physically impossible.

## 2. Quick Start (Run the Audit)
Find your analytic boundary and view the forensic dashboard in seconds.

```bash
# Clone and Enter
git clone https://github.com/Corusant-world/ctdr-maxwell-audit.git && cd ctdr-maxwell-audit

# Launch the Maxwell Dashboard (GUI)
# Windows:
start maxwell_dashboard/index.html
# macOS/Linux:
open maxwell_dashboard/index.html
```

## 3. Example Output (Forensic Trace)
When auditing a standard Blackwell-class inference stack at scale:

```text
[00:00:00] Target: N=500,000 (fp16)
[00:00:01] Required HBM: ~500 GB
[00:00:02] Available HBM: 80 GB (H100)
[00:00:03] Status: [PHYSICAL OOM IMMINENT]
[04:00:00] Entropy Accumulation: 85%
[04:05:00] Logic State: [STOCHASTIC COLLAPSE DETECTED]
[RESULT] : Mission Failure via Logic Leakage.
```

## 4. Why this exists
1. **The NxN Wall:** To prove that current "scaling laws" ignore HBM physical limits.
2. **Deterministic Invariants:** To provide a solution (CTDR) that maintains 100% logic consistency at 67°C.
3. **Receipts over Vibes:** To ship real NVML energy/telemetry artifacts instead of marketing claims.

## 5. Success Criteria
Maxwell is successful if:
- You can answer "when will my robot hallucinate due to thermal jitter?" within seconds.
- You reduce your R&D "Stochastic Tax" by enforcing p-adic invariants.

## 6. AI Assistance Disclaimer
This project was developed with assistance from AI/LLMs (Cursor, Gemini-1.5-Pro), supervised by an engineer who believes that **light speed is never fast enough**.

---

## Technical Inquiry
Seeking a technical deep-dive with infrastructure owners (Inference/Retrieval/Perf). 
- **Lead:** [Stanislav Byriukov]
- **Focus:** Deterministic substrates & high-density GPU orchestration.
