# Reddit post draft (public-safe)

## Suggested subreddits (must follow their rules)
- r/MachineLearning
- r/LocalLLaMA

## Title options
- [R] Evidence-first: fp16 N x N materialization hits an HBM wall (H100) — public-safe pack + comparator
- Evidence pack: OOM boundary (analytic) + receipts/artifacts + local dashboard (no kernel code)

## Body (edit brackets only)

I’m posting an evidence-first “feasibility boundary” packet: fp16 **N x N** similarity/attention materialization has a hard HBM wall (bytes, not opinions). If you need N x N materialization, you eventually lose to memory capacity/bandwidth.

The packet is public-safe: 2 graphs + JSON artifacts + a local, clickable dashboard + a pack comparator. No kernel source / PTX / SASS / bindings.

3 links:
- Preprint (arXiv): <LINK_ARXIV>
- Evidence bundle (evidence.zip): <LINK_EVIDENCE_ZIP>
- Repo/release (dashboard + tools): <LINK_REPO_OR_RELEASE>

What’s in the evidence.zip:
- `graph_oom_wall.png` (OOM wall visual)
- logs + repro scripts (public-safe)
- example NVML receipt artifacts (power/util/temp + integrated Joules)
- dashboard + pack comparator (upload two `summary_public.json` and compare)

Questions for the community (so this doesn’t turn into vibes):
1) For long-context / retrieval-heavy inference, what is the fairest baseline definition for “useful query” (accuracy + cost) you’d accept in a public pack?
2) Which public benchmarks capture the *exactness vs cost* tradeoff without hiding behind ANN approximations?
3) If you have an alternative approach that avoids N x N materialization: would you submit a `summary_public.json` pack so we can compare in the same UI?

Practical ask: I’m trying to route this to the right owner (inference/retrieval/GPU memory/perf) for a 20–30 min technical screen **before Dec 31**.

Commitment: this is a **time‑boxed evaluation window**; **Dec 31 is the cut‑off**. After that I proceed with other partners. Public-safe packet stays public; no source handover.



