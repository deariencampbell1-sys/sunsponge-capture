"""Walk-mode spine smoke tests — pure import checks, no browser, no network.

These are the guardrails workers W1-W7 must not break. If any of these fail
after a worker lands their PR, the spine is corrupted.
"""

from __future__ import annotations

import importlib

import pytest


# ---------------------------------------------------------------------------
# Package tree — every spine module must import cleanly with no side effects.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "module_name",
    [
        "capturd",
        "capturd.shots",
        "capturd.walk",
        "capturd.walk.schema",
        "capturd.walk.viewer",
        "capturd.walk.voice",
        "capturd.walk.recorder",
        "capturd.walk.ai_pipeline",
        "capturd.walk.coordinator",
        "capturd.mcp",
        "capturd.mcp.server",
        "capturd.cli",
        "capturd.walk.cli",
    ],
)
def test_module_imports_clean(module_name: str) -> None:
    """Every spine module must be importable without side effects or errors."""
    importlib.import_module(module_name)


# ---------------------------------------------------------------------------
# Schema — the contract every worker depends on. Do not break these shapes.
# ---------------------------------------------------------------------------


def test_schema_dataclasses_construct() -> None:
    from capturd.walk.schema import (
        AIAnnotations,
        AnimationKeyframe,
        BoundingRect,
        CameraAction,
        ContentMetadata,
        ContentMode,
        CursorPoint,
        DemoSpec,
        DemoStep,
        Hotspot,
        Interaction,
        WordTimestamp,
        ZoomTarget,
    )

    # Round-trip a minimal DemoSpec through to_dict()
    spec = DemoSpec(id="t1", name="test", goal="prove the spine holds")
    assert spec.version == 1
    assert spec.viewport == {"width": 1440, "height": 900}
    assert spec.to_dict()["id"] == "t1"

    # DemoStep with content-mode defaults
    step = DemoStep(
        index=0,
        timestamp=0,
        pageUrl="https://example.com",
        pageTitle="Example",
        interaction=Interaction(type="click", target={}, hotspot={"xPct": 50, "yPct": 50}),
    )
    assert step.contentMode == ContentMode.DOM.value
    assert step.voiceoverWords is None

    # Semantic zoom target
    zt = ZoomTarget(selector="#buy-now")
    assert zt.level == 1.5
    assert zt.easing == "ease-in-out"

    # Camera keyframe
    kf = AnimationKeyframe(stepIndex=0, action=CameraAction.ZOOM_TO.value, target="#buy-now")
    assert kf.duration == 500

    # Voice-sync primitive
    wt = WordTimestamp(word="Buy", tStartMs=100, tEndMs=250)
    assert wt.tEndMs - wt.tStartMs == 150

    # Cursor point
    cp = CursorPoint(x=100.0, y=200.0, t=50)
    assert cp.t == 50

    # Content metadata
    cm = ContentMetadata(hasCanvas=True, canvasAreaPct=42.5)
    assert cm.hasCanvas
    assert cm.canvasAreaPct == 42.5

    # AI annotations envelope
    ai = AIAnnotations(summary="A flow.", style="cinematic")
    assert ai.animationTimeline == []

    # Bounding rect
    br = BoundingRect(x=0, y=0, width=100, height=50)
    assert br.width == 100

    # Hotspot
    hs = Hotspot(xPct=50.0, yPct=25.0)
    assert hs.xPct == 50.0


# ---------------------------------------------------------------------------
# Viewer template — must ship inside the package (package_data).
# ---------------------------------------------------------------------------


def test_viewer_template_ships_with_package() -> None:
    from capturd.walk.viewer import default_template_path

    p = default_template_path()
    assert p.is_file(), f"viewer template missing: {p}"
    # Basic sanity — must contain the placeholder script block.
    text = p.read_text(encoding="utf-8")
    assert '<script id="demo-data"' in text, "viewer template missing demo-data placeholder"


# ---------------------------------------------------------------------------
# CLI dispatcher — help + version + subcommand routing don't crash.
# ---------------------------------------------------------------------------


def test_cli_help_runs() -> None:
    from capturd.cli import main

    assert main(["--help"]) == 0
    assert main(["-V"]) == 0


def test_cli_unknown_mode_errors() -> None:
    from capturd.cli import main

    assert main(["nonsense-mode"]) == 2


def test_walk_cli_help() -> None:
    """`capturd walk --help` must render argparse without crashing."""
    import argparse

    from capturd.walk.cli import _build_parser

    parser = _build_parser()
    assert isinstance(parser, argparse.ArgumentParser)
    # Verify all expected subcommands wire up
    subs = parser._subparsers._actions[-1].choices  # type: ignore[attr-defined]
    for expected in ("record", "stop", "status", "list", "export", "edit", "delete"):
        assert expected in subs, f"walk subcommand missing: {expected}"
