# Release assets checklist (do NOT publish automatically)

## Assets to attach to GitHub Release

Preprint (pick one):
- `papers/arxiv_ctdr_oom_ultrametric_memory/main.pdf`
- `papers/arxiv_ctdr_oom_ultrametric_memory_upload.zip`

Evidence bundle:
- `evidence_public/evidence.zip` (build via `python scripts/build_evidence_zip.py`)

Maxwell dashboard (optional, narrative-first):
- `maxwell_dashboard/index.html` (host as GitHub Pages)

Proof clip:
- (optional) short proof clip mp4 (attach as Release asset)

## Post-release: copy the 3 asset URLs

After creating the Release, paste URLs into:
- `posts/RELEASE_NOTES_D0.md`
- `posts/POST_HN.md`
- `posts/POST_REDDIT.md`
- `posts/POST_X_THREAD.md`

## Sanity command (optional)

Generate file sizes + short hashes (for internal sanity, not required for public):

```bash
python -c "from pathlib import Path; import hashlib; paths=[Path('assets/graph_oom_wall.png'),Path('assets/graph_joules_per_query.png'),Path('assets/summary_public.json'),Path('assets/B_compare.json'),Path('evidence_public/evidence.zip')];\nfor p in paths:\n  print(p,'MISSING') if not p.exists() else print(f\"{p} | {p.stat().st_size/1024/1024:.2f} MB | sha256[:16]={hashlib.sha256(p.read_bytes()).hexdigest()[:16]}\")"
```



