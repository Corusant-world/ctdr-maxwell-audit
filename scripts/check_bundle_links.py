#!/usr/bin/env python3
"""
Offline bundle checker for `public_release_maxwell/`.

Goals:
- Prevent "yesterday worked / today broken" regressions.
- Ensure dashboard href/src are resolvable within the public bundle.
- Ensure the public bundle contains no internal-path leaks (examples: internal build roots, private repo paths).

No external dependencies.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]  # public_release_maxwell/
SELF = Path(__file__).resolve()

HTML_FILES = [
    ROOT / "maxwell_dashboard" / "index.html",
    ROOT / "maxwell_dashboard" / "compare.html",
]

BANNED_SUBSTRINGS = [
    # Internal/private path examples that must not appear in the public bundle.
    "partner_packet_nvidia",
    "integrations/benchmarks_scale",
    "../integrations",
    "tech-eldorado-infrastructure",
    "prototypes/prototype_ctdr",
    "cursor-plan://",
    ".cursor",
    "file:///",
    "C:\\Users\\",
    "/Users/",
]

_HREF_SRC_RE = re.compile(r'''(?:href|src)\s*=\s*["']([^"']+)["']''')


def _iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file():
            yield p


def _check_banned_strings() -> list[str]:
    errors: list[str] = []
    for p in _iter_files(ROOT):
        if p.resolve() == SELF:
            continue
        # Skip binary-ish assets.
        if p.suffix.lower() in {".png", ".zip", ".jpg", ".jpeg", ".gif", ".webp", ".mp4"}:
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for s in BANNED_SUBSTRINGS:
            if s in txt:
                errors.append(f"BANNED_STRING: {s} in {p.relative_to(ROOT).as_posix()}")
    return errors


def _check_html_links() -> list[str]:
    errors: list[str] = []
    for html in HTML_FILES:
        if not html.exists():
            errors.append(f"MISSING_HTML: {html.relative_to(ROOT).as_posix()}")
            continue
        txt = html.read_text(encoding="utf-8", errors="replace")
        refs = _HREF_SRC_RE.findall(txt)
        for r in refs:
            if r.startswith(("http://", "https://", "mailto:", "#")):
                continue
            # Relative to the html file.
            target = (html.parent / r).resolve()
            if not target.exists():
                errors.append(
                    f"BROKEN_LINK: {html.relative_to(ROOT).as_posix()} -> {r} (missing {target})"
                )
    return errors


def _check_pack_paths() -> list[str]:
    errors: list[str] = []
    sp = ROOT / "assets" / "summary_public.json"
    if not sp.exists():
        return [f"MISSING: assets/summary_public.json"]
    try:
        import json

        d = json.loads(sp.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"INVALID_JSON: assets/summary_public.json ({e})"]

    src_path = (d.get("source") or {}).get("path")
    if isinstance(src_path, str) and src_path:
        if not (ROOT / src_path).exists():
            errors.append(f"PACK_SOURCE_MISSING: source.path={src_path}")

    memo_path = (((d.get("tracks") or {}).get("memoization_prefix_range") or {}).get("source") or {}).get("path")
    if isinstance(memo_path, str) and memo_path:
        if not (ROOT / memo_path).exists():
            errors.append(f"PACK_TRACK_MISSING: tracks.memoization_prefix_range.source.path={memo_path}")

    return errors


def main() -> int:
    errors: list[str] = []
    errors += _check_banned_strings()
    errors += _check_html_links()
    errors += _check_pack_paths()

    if errors:
        print("FAIL")
        for e in errors:
            print(e)
        return 2

    print("PASS: bundle is self-contained, links resolve, and no internal paths leaked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


