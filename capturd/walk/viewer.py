r"""Viewer renderer — turn a DemoSpec (dict) into the self-contained HTML page.

The viewer template (``templates/viewer.html``) ships with the package as
``package_data``. It contains a placeholder ``<script id="demo-data">`` block
that gets replaced with the actual demo JSON at render time.

Design notes:

* The output is a single self-contained file (zero deps, works from ``file://``).
* Screenshots + voiceover audio should be inlined as base64 BEFORE rendering.
  See ``coordinator.DemoForge._inline_screenshots`` for the inlining routine —
  callers can reuse it or do their own.
* The substitution uses ``re.sub`` with a lambda so JSON backslash sequences
  (``\1``, ``\g<name>``, screenshot paths on Windows) are NOT interpreted by
  the regex engine.
* Line endings on write are LF for cross-platform portability — the template's
  regex depends on it.

This module is the authoritative renderer. ``DemoForge.export_demo`` has its
own copy of the substitution for now (see coordinator.py); W1/W2 workers may
consolidate on this function.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


_SCRIPT_BLOCK_RE = re.compile(
    r'<script id="demo-data"[^>]*>\s*\n.*?\n\s*</script>',
    re.DOTALL,
)


class ViewerRenderError(RuntimeError):
    """Raised when the template is missing or malformed."""


def default_template_path() -> Path:
    """Path to the packaged viewer template."""
    return Path(__file__).resolve().parent / "templates" / "viewer.html"


def render_viewer(
    spec: dict[str, Any],
    *,
    template_path: Path | None = None,
) -> str:
    """Render a DemoSpec (as dict) into a self-contained HTML string.

    Parameters
    ----------
    spec:
        A ``DemoSpec.to_dict()`` payload. Screenshots + audio should already
        be inlined as base64 if you want a portable single-file result.
    template_path:
        Override the packaged template. Defaults to
        ``capturd/walk/templates/viewer.html``.

    Returns
    -------
    The rendered HTML as a UTF-8 string. Caller is responsible for writing it
    to disk with LF line endings (``.encode("utf-8")`` + ``write_bytes``).
    """
    tpath = template_path or default_template_path()
    if not tpath.is_file():
        raise ViewerRenderError(f"viewer template not found: {tpath}")

    template = tpath.read_text(encoding="utf-8")
    if not _SCRIPT_BLOCK_RE.search(template):
        raise ViewerRenderError(
            'viewer template missing <script id="demo-data"> placeholder block'
        )

    spec_json = json.dumps(spec, indent=2)
    new_block = (
        f'<script id="demo-data" type="application/json">\n{spec_json}\n  </script>'
    )
    # Lambda replacement — do NOT let re.sub interpret backslash escapes.
    return _SCRIPT_BLOCK_RE.sub(lambda _m: new_block, template, count=1)


def render_viewer_to_file(
    spec: dict[str, Any],
    out_path: Path,
    *,
    template_path: Path | None = None,
) -> Path:
    """Convenience: render and write in one call. Returns the output path."""
    html = render_viewer(spec, template_path=template_path)
    out_path.write_bytes(html.encode("utf-8"))
    return out_path


__all__ = [
    "ViewerRenderError",
    "default_template_path",
    "render_viewer",
    "render_viewer_to_file",
]
