"""
Build a public-safe evidence.zip for the forcing package.

Principles:
- Only include artifacts (JSON/MD/LOG/TXT/PNG/MP4/PDF) that do NOT expose kernel source,
  PTX/SASS, or bindings code.
- Keep this repo self-contained: only include files under this public bundle.

Output:
- evidence_public/evidence.zip
- evidence_public/README.md (must exist)
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from typing import Iterable, List


REPO_ROOT = Path(__file__).resolve().parents[1]  # public_release_maxwell/
ASSETS_DIR = REPO_ROOT / "assets"
EVIDENCE_PUBLIC = REPO_ROOT / "evidence_public"
DASHBOARD_DIR = REPO_ROOT / "maxwell_dashboard"
CHALLENGE_DIR = REPO_ROOT / "babel_challenge"
PACK_FORMAT_DIR = REPO_ROOT / "pack_format"
PACK_TOOLS_DIR = REPO_ROOT / "pack_tools"
POSTS_DIR = REPO_ROOT / "posts"


def _rel(p: Path) -> str:
    return p.relative_to(REPO_ROOT).as_posix()


def _collect_existing(paths: Iterable[Path]) -> List[Path]:
    out: List[Path] = []
    for p in paths:
        if p.exists() and p.is_file():
            out.append(p)
    return out


def _glob_dir(base: Path, pattern: str) -> List[Path]:
    if not base.exists():
        return []
    return [p for p in base.glob(pattern) if p.is_file()]


def main() -> int:
    # Must have README.md present (committed), zip is generated.
    readme = EVIDENCE_PUBLIC / "README.md"
    if not readme.exists():
        print(f"ERROR: missing {readme}. Create it first.", file=sys.stderr)
        return 2

    # Create output folder.
    EVIDENCE_PUBLIC.mkdir(parents=True, exist_ok=True)

    out_zip = EVIDENCE_PUBLIC / "evidence.zip"

    files: List[Path] = []

    # 1) Assets (PNG graphs + packs)
    files += _collect_existing(
        [
            ASSETS_DIR / "graph_oom_wall.png",
            ASSETS_DIR / "graph_joules_per_query.png",
            ASSETS_DIR / "summary_public.json",
            ASSETS_DIR / "summary_public.js",
            ASSETS_DIR / "memoization_prefix_range.json",
            ASSETS_DIR / "B_compare.json",
        ]
    )

    # 2) Maxwell dashboard (static narrative; public-safe)
    files += _glob_dir(DASHBOARD_DIR, "*.html")
    files += _glob_dir(DASHBOARD_DIR, "*.css")
    files += _glob_dir(DASHBOARD_DIR, "*.js")
    files += _glob_dir(DASHBOARD_DIR, "*.md")

    # 3) Babel challenge runner (procedural dataset + harness; public-safe)
    files += _glob_dir(CHALLENGE_DIR, "*.py")
    files += _glob_dir(CHALLENGE_DIR, "*.md")

    # 4) Pack Standard v1 (schema + tools) for community submissions
    files += _glob_dir(PACK_FORMAT_DIR, "*.md")
    files += _glob_dir(PACK_FORMAT_DIR, "*.json")
    files += _glob_dir(PACK_TOOLS_DIR, "*.py")

    # 5) Posts (public copy, ready to paste)
    files += _glob_dir(POSTS_DIR, "*.md")

    # 6) Include README at the root of the zip as entry point.
    files.append(readme)

    # De-duplicate
    uniq: List[Path] = []
    seen = set()
    for p in files:
        rp = str(p.resolve())
        if rp in seen:
            continue
        seen.add(rp)
        uniq.append(p)

    # Build zip
    if out_zip.exists():
        out_zip.unlink()

    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in uniq:
            # Place README at zip root; others under their repo-relative paths.
            arc = "README.md" if p == readme else _rel(p)
            z.write(p, arcname=arc)

    print(f"OK: wrote {out_zip} ({len(uniq)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



