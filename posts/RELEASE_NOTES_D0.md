# Release Notes (D0) — Public-safe “3-link forcing package”

**Hard rule:** public-safe only. No CUDA kernel source / PTX / SASS / bindings.

## 0) The “3 links” (paste these 3 everywhere)

- **Link #1 (Preprint / priority)**: `<LINK_ARXIV>`
- **Link #2 (Evidence bundle / evidence.zip)**: `<LINK_EVIDENCE_ZIP>`
- **Link #3 (Repo/release / dashboard + tools)**: `<LINK_REPO_OR_RELEASE>`

Optional:
- **Proof clip (60–90s)**: `<LINK_CLIP_OPTIONAL>`

## 1) What this is (one paragraph)

This release is an evidence-first packet: a reproducible **OOM wall** (physical memory constraint for explicit fp16 N x N materialization), plus a public-safe view of a deterministic retrieval primitive with real **NVML energy receipts**.

The goal is not “marketing”. The goal is **routing**: “who owns this problem?” → 20–30 min technical screen.

Claim (scoped, measurable): receipts and artifacts make tradeoffs inspectable (exactness vs cost). Publicly I avoid “orders of magnitude” claims unless receipts demonstrate it.

## 2) What’s inside (public-safe)

### 2.1 Graphs (PNG)

- OOM wall: `assets/graph_oom_wall.png`
- Energy per query (measured NVML): `assets/graph_joules_per_query.png`

### 2.2 Evidence bundle

`evidence.zip` includes:
- `assets/summary_public.json` (Pack Standard v1 summary)
- `assets/B_compare.json` (example AB artifact used by the dashboard)
- `assets/memoization_prefix_range.json` (M≪N work-shrink track)

### 2.3 Maxwell dashboard (narrative-first)

Optional (static HTML):
- `maxwell_dashboard/index.html`

## 3) What I claim (and what I do NOT claim)

### Claims (with artifacts)

- **OOM wall is real**: explicit fp16 N x N materialization becomes physically infeasible at large N (HBM limit).  
  See: `assets/graph_oom_wall.png` (analytic) + `assets/B_compare.json` (measured pack metadata) + receipts in `assets/summary_public.json`.

- **Energy receipts exist (NVML)**: power/util/temp + Joules integration is captured in JSON and can be verified.  
  See: `assets/summary_public.json` (includes telemetry) and `assets/B_compare.json` (AB artifact).

### Non-claims (explicitly NOT asserting here)

- I am not claiming “AGI”, “zero hallucinations”, or “Landauer marketing proofs”.
- I am not claiming end-to-end dominance on cold full-scan QPS across all baselines.
- I am not claiming flight readiness or real-time autonomy from this public-safe packet.

## 4) The ask (copy/paste)

**Ask:** routing to the owner → 20–30 min technical screen.  
If the owner is interested: NDA → 14-day remote pilot (no repo handover; black-box binary allowed).



