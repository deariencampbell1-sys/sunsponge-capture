"""Voice loop — push-to-talk + Whisper STT + TTS reply.

The whole point: you watch the agent walk the flow AND you talk to it about
what you see. "Top left is X, Y, Z — pan in on this before you click Buy Now."
The agent hears you (Whisper), understands (LLM through gateway), acts
(camera keyframes / next-click choice), and replies (TTS, ducked over the
site audio if any).

Modes:

* **Push-to-talk overlay.** Recording page has a mic button in the overlay
  badge; hold to speak, release to send. Transcript → agent prompt.
* **Workflow mode.** Agent watches the user click each step; between clicks
  the agent asks "what are you trying to illustrate?" via TTS; user answers
  by voice; agent extracts intent and writes it into the DemoSpec goal +
  per-step annotation.
* **Continuous listen (optional).** Streaming mic → Whisper streaming →
  agent hears real-time. Off by default; opt-in per session.

Tech:

* STT: ``faster-whisper`` (CT2 backend, ~5× openai-whisper, works offline
  with the small.en model — good enough for spoken direction).
* Audio input: ``sounddevice`` (portaudio) for cross-platform mic capture.
* TTS reply: reuse the AI pipeline's edge-tts pipe (same voice as narration
  so the agent sounds like the demo narrator).

This is a SPINE STUB. The real implementation lands in **W6**.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

logger = logging.getLogger(__name__)


class VoiceLoopError(RuntimeError):
    """Raised when the voice pipeline cannot start (mic, model, or model download)."""


@dataclass
class VoiceConfig:
    """Runtime config for the voice loop."""

    model: str = "small.en"          # faster-whisper model size
    device: str = "auto"             # 'auto' | 'cpu' | 'cuda'
    compute_type: str = "int8"       # CT2 quantization — int8 is fine on CPU
    input_device: int | None = None  # sounddevice input index (None = default)
    sample_rate: int = 16000
    workflow_mode: bool = False      # agent narrates + asks questions between clicks
    continuous: bool = False         # streaming mic instead of push-to-talk


# TODO(W6): implement the push-to-talk lifecycle.
#
# API sketch the recorder + MCP surface expect:
#
#   loop = VoiceLoop(config=VoiceConfig(workflow_mode=True))
#   await loop.start(on_utterance=lambda text: recorder.inject_direction(text))
#   ...
#   await loop.stop()
#
# The on_utterance callback receives clean transcripts; the loop handles VAD,
# mic gating, and Whisper decoding off the main thread.
class VoiceLoop:
    """Placeholder — the spine defines the contract; W6 fills in the body."""

    def __init__(self, config: VoiceConfig | None = None) -> None:
        self.config = config or VoiceConfig()
        self._running = False

    async def start(self, on_utterance: Callable[[str], Any]) -> None:
        raise NotImplementedError(
            "voice loop lands in W6 (Whisper + sounddevice + TTS reply). "
            "Spine only defines the contract."
        )

    async def stop(self) -> None:
        raise NotImplementedError("W6")


__all__ = ["VoiceConfig", "VoiceLoop", "VoiceLoopError"]
