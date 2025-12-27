## Maxwell Dashboard (David vs Goliath) — public-safe, narrative-first

This is a **static** split-screen dashboard intended to be opened locally or hosted as GitHub Pages.

### What it is

- **Left**: "Status Quo" baseline (measured: `vector_scan` run on the same H100).
- **Right**: Omega/CTDR run (measured: `ctdr` run).
- **Top**: the feasibility boundary (**OOM wall**) and measured **energy receipts**.
- **Everything clickable**: every metric links to the underlying artifact.

### What it is NOT

- Not a claim about "Landauer limit", "entropy 1e9×", or "NFTs".
- Not a claim about "8–10× H100 cluster HNSW collapse" unless I publish a measured artifact for it.

### How it gets its numbers

The dashboard reads:

- `../assets/summary_public.js` (Pack Standard v1, bundled)
- `../assets/graph_oom_wall.png`
- `../assets/graph_joules_per_query.png`

Regenerate:

```bash
python scripts/build_public_assets.py
python scripts/build_evidence_zip.py
```

### How to open

Open in a browser:

- `maxwell_dashboard/index.html`
- `maxwell_dashboard/compare.html` (load 2 `summary_public.json` files and compare)

No server is required (I avoid `fetch()` so `file://` works).


