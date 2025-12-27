# Forcing Package Runbook (public‑safe) — “3 links” used everywhere

**Goal:** make NVIDIA routing effortless: anyone can forward 1 short message internally and the recipient can validate quickly.

**Hard rules:**
- No DPX kernel source / PTX / SASS / bindings.
- No repo handover before definitive agreement.
- Public‑safe only: graphs, aggregate metrics, methodology, NDA plan.

---

## 1) The “3‑link package” (same 3 items in every channel)

1) **Preprint package (priority / public proof)**
- Local artifact: `papers/arxiv_ctdr_oom_ultrametric_memory_upload.zip`
- Local PDF: `papers/arxiv_ctdr_oom_ultrametric_memory/main.pdf`
- arXiv URL: (fill after submission) `https://arxiv.org/abs/<ID>`

2) **Evidence bundle (public‑safe)**
- `public_release_maxwell/evidence_public/evidence.zip` (graphs + artifacts + dashboard + tools)

3) **Repo/release (links + updates)**
- GitHub release/repo link (the stable place to route people)

Optional:
4) **60–90s proof clip**

Rule: the two graphs must be viewable without reading code:
- Graph 1: **OOM wall** — memory scaling N^2 vs O(N) (analytic boundary)
- Graph 2: **Energy per useful query** — J/query vs method (from receipts in the pack)

Clip rules (if you publish it):
- Show `nvidia-smi` live + running benchmark + final JSON output.
- No kernel source on screen.

---

## 2) How to produce the 2 graphs (fast, public‑safe)

### Option A (fastest): take 2 screenshots from the PDF
1) Open `papers/arxiv_ctdr_oom_ultrametric_memory/main.pdf`
2) Capture the two figure pages as images (PNG)
3) Save as:
- `assets/graph_oom_wall.png`
- `assets/graph_joules_per_query.png`

### Option B (better): export pages from PDF to PNG
Use any available tool (pick one):
- `pdftoppm` (Poppler)
- ImageMagick (`magick`)

Example (ImageMagick):
```bash
magick -density 200 papers/arxiv_ctdr_oom_ultrametric_memory/main.pdf[<page>] assets/graph_oom_wall.png
magick -density 200 papers/arxiv_ctdr_oom_ultrametric_memory/main.pdf[<page>] assets/graph_joules_per_query.png
```

---

## 3) How to record the 60–90s clip (Windows‑friendly)

**Goal for the clip:** a viewer must see:
1) GPU identity + power/util (nvidia-smi)
2) A benchmark run command
3) The resulting JSON metrics line(s)

### Minimal script for the terminal
In one terminal pane, run:
```bash
nvidia-smi --query-gpu=name,power.draw,utilization.gpu,clocks.sm,memory.used --format=csv -l 1
```

In another pane, run the benchmark (choose the public‑safe one you want to show) and end by printing the results JSON location.

### Recording
Use Xbox Game Bar (no installs):
- Start/stop recording: **Win + Alt + R**

**Hard rule:** do not show source code of kernels/bindings.

---

## 4) The ask (paste as the last 2 lines everywhere)

**Ask:** 20–30 min technical screen → NDA → 14‑day remote pilot.  
Under NDA: container/runbook + evidence bundle; no repo handover.

---

## 5) Copy‑paste “routing message” (public‑safe, short)

Subject/first line:
**Routing request: H100 retrieval primitive (OOM wall + energy per query) — seeking owner before Dec 31**

Body (edit brackets only):
- Preprint (priority): [arXiv link]
- Evidence bundle (evidence.zip): [link]
- Repo/release (dashboard + tools): [link]
- Optional clip (60–90s): [link]
- Ask: 20–30 min screen → NDA → 14‑day pilot (no repo handover)

Commitment line (one sentence, no drama):
- Time‑boxed evaluation window ends **Dec 31**. After that I proceed with other partners. Public-safe packet stays public; no source handover.


