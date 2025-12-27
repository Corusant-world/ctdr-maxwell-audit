## Pack Standard v1 (public-safe)

This repo uses a small public-safe “pack” format so anyone can publish H100 results and compare apples-to-apples.

### What a “pack” is

A pack is an **evidence bundle** (zip or folder) that contains:

- `assets/summary_public.json` (**required**)
- `receipt_energy.json` (**recommended**: NVML / nvidia-smi receipts)
- `nvidia_smi_before.txt` / `nvidia_smi_after.txt` (**recommended**)
- `receipt_hashes.json` (**required**: sha256 of the above + key artifacts)
- plus whatever artifacts produced these numbers (logs, benchmark JSON, etc).

### Submission checklist (5 lines)

1) Run your H100 workload and capture receipts: `receipt_energy.json` + `nvidia_smi_before.txt`/`nvidia_smi_after.txt`.
2) Produce `summary_public.json` in **Pack Standard v1** format (schema = `sigma_summary_public_v1`).
3) Produce `receipt_hashes.json` with sha256 for the summary + receipts (+ your key result JSON).
4) Zip the pack (or publish a folder) and share it.
5) Compare vs another pack in `maxwell_dashboard/compare.html` (upload two `summary_public.json` files).

### What counts as win (2 lines)

- **Win** = better energy/speed **without losing exactness**: \(top1\_accuracy = 1.0\) stays, while \(J/query\) and/or \(p95\) improve.
- **Not a win** = faster/cheaper but accuracy drops (or workload/baseline is undefined / receipts missing).

### Why `summary_public.json`

It’s a compact summary that the Maxwell dashboard can load locally (no server) and compare.

### Validation

Use:

- `pack_tools/validate_summary_public.py`

### Schema

See:

- `pack_format/summary_public.schema.json`


