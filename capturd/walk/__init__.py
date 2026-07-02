"""Walkthrough mode — agent-made interactive product demos.

The `walk` subpackage records a user flow (or has an agent walk it) and produces
a self-contained viewer HTML plus an MP4 export. Beat-for-beat differentiators
vs Supademo / Arcade / Storylane:

- Agent-made, not human-recorded (LLM step-picker drives Playwright headful)
- Live DOM via rrweb, not static screenshots (survives site changes)
- Semantic zoom via panzoom (element-anchored, not pixel-anchored)
- Voice-synced camera (TTS word timestamps -> keyframe alignment)
- Content-mode auto-detection (DOM / video / hybrid for canvas + games)
- Agent-editable timeline via MCP (`demo.zoom`, `demo.pan`, `demo.hold`, ...)
"""
