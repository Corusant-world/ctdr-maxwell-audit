# Hacker News post draft (public-safe)

**Title options (pick one):**
- Show HN: Evidence bundle + dashboard for the fp16 N x N “OOM wall” (H100) + pack comparator (no kernel code)
- Show HN: Public-safe artifacts for long-context compute constraints (OOM boundary + NVML receipts + comparator)

**Body (edit brackets only):**

This is an evidence-first packet about a simple constraint: fp16 **N x N** similarity/attention materialization has a hard HBM ceiling (it’s bytes, not opinions). At N=500,000 you’re at 250B elements → ~500 GB just to store the matrix, so “materialize N x N” is not even on the table for 80GB HBM.

What I’m actually publishing is a **public-safe** bundle: two graphs + JSON/log artifacts + a local, clickable dashboard + a pack comparator. No kernel source / PTX / SASS / bindings.

Links:
- Preprint (arXiv): <LINK_ARXIV>
- Evidence bundle (evidence.zip): <LINK_EVIDENCE_ZIP>
- Repo/release (includes the dashboard + tools): <LINK_REPO_OR_RELEASE>

5-minute verification checklist (no GPU required):
- Open `evidence.zip` and view `assets/graph_oom_wall.png`
- Open `maxwell_dashboard/index.html` locally (static HTML)
- Open `maxwell_dashboard/compare.html` and upload `assets/summary_public.json`
- Validate pack format: `pack_tools/validate_summary_public.py` vs `pack_format/summary_public.schema.json`

Notes:
- The “OOM wall” chart is an analytic boundary (fp16 bytes = N^2 * 2); it’s meant to stop unproductive “bench wars”.
- NVML receipts exist as artifacts in the pack; I’m not asserting “orders of magnitude” publicly unless the receipts show it.
- The dashboard is intentionally dumb (static HTML) so it can’t hide anything behind servers or “trust me”.

Ask: I’m trying to route this to the right owner (inference/retrieval/GPU memory/perf) for a 20–30 min technical screen **before Dec 31**.

Commitment: this is a **time‑boxed evaluation window**; **Dec 31 is the cut‑off**. After that I proceed with other partners. Public-safe packet stays public; no source handover.

If you have feedback on what a fair “pack” should contain (metrics/receipts/definitions), I’ll incorporate it.



