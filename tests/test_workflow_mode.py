"""Tests for W7 workflow mode — agent asks intent between clicks.

Workflow mode: after each captured click, the recorder pauses, asks the user
"what are you illustrating?" via TTS (voice_loop.reply), captures the spoken
answer (voice_loop.push_to_talk, 8s window), and persists it as
``step.userIntent`` + ``step.annotation [user intent: ...]``.

Tests:

1. Three-click flow through a fixture HTML page → each step gets userIntent.
2. Workflow mode without voice → raises DemoRecorderError.
3. Empty transcript (user says nothing) → no crash, userIntent stays None.
4. VoiceLoop.reply / push_to_talk called in correct sequence.
"""

from __future__ import annotations

import asyncio
import json
import logging
import wave
from pathlib import Path
from unittest import mock

import numpy as np
import pytest

from capturd.walk.recorder import DemoManager, DemoRecorder, DemoRecorderError
from capturd.walk.schema import DemoStep, Interaction
from capturd.walk.voice import VoiceConfig


# ---------------------------------------------------------------------------
# Stub VoiceLoop — no real mic / TTS, returns canned transcripts.
# ---------------------------------------------------------------------------

class StubVoiceLoop:
    """A VoiceLoop stand-in for workflow-mode tests.

    ``reply()`` is a no-op. ``push_to_talk()`` returns the next transcript
    from ``transcripts`` in FIFO order. This is the seam the brief allows:
    we inject a stub so the recorder logic runs for real without hardware.
    """

    def __init__(self, transcripts: list[str] | None = None) -> None:
        self._transcripts: list[str] = list(transcripts or [])
        self._idx = 0
        self._running = False
        self.reply_calls: list[str] = []         # recorded for assertions
        self.push_to_talk_calls: list[int] = []   # duration_ms values

    async def start(self, on_utterance=None, page=None) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False

    async def reply(self, text: str) -> None:
        self.reply_calls.append(text)

    async def push_to_talk(self, duration_ms: int | None = None) -> str:
        self.push_to_talk_calls.append(duration_ms or 0)
        if self._idx < len(self._transcripts):
            t = self._transcripts[self._idx]
            self._idx += 1
            return t
        return ""


# ---------------------------------------------------------------------------
# Helpers — build click payloads matching what the overlay JS emits.
# ---------------------------------------------------------------------------

def _make_click_payload(
    selector: str,
    text: str = "",
    page_url: str = "http://localhost:8765/test.html",
    page_title: str = "Test Page",
) -> dict:
    return {
        "type": "click",
        "target": {
            "selector": selector,
            "tagName": "button",
            "text": text,
            "boundingRect": {"x": 100, "y": 200, "width": 80, "height": 40},
        },
        "hotspot": {"xPct": 50, "yPct": 50},
        "pageUrl": page_url,
        "pageTitle": page_title,
        "timestamp": 1000,
    }


# ---------------------------------------------------------------------------
# Test 1: 3-click workflow mode — each step gets userIntent.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_workflow_three_clicks_store_user_intent(tmp_path: Path) -> None:
    """Three clicks in workflow mode → each step has userIntent + annotation."""
    transcripts = [
        "I want to show pricing",
        "This is the CTA",
        "Confirmation screen",
    ]
    stub = StubVoiceLoop(transcripts=transcripts)

    # Build a recorder by hand — no browser needed for this logic test.
    recorder = DemoRecorder(
        session_id="wf-test-001",
        url="http://localhost:8765/test.html",
        name="Workflow Test",
        goal="Test workflow mode",
        output_dir=tmp_path / "demos",
        workflow_mode=True,
    )
    recorder.voice_loop = stub  # type: ignore[assignment]

    # Mock the page so _capture_loop doesn't crash on screenshots / evaluate.
    mock_page = mock.AsyncMock()
    mock_page.screenshot.return_value = b"\x89PNG\r\n\x1a\n"  # minimal PNG
    mock_page.evaluate.return_value = None
    mock_page.url = "http://localhost:8765/test.html"
    recorder._page = mock_page  # type: ignore[assignment]

    recorder._started_at_ms = 1000
    recorder._capture_task = asyncio.create_task(
        recorder._capture_loop(), name="wf-test-cap"
    )

    # Feed 3 clicks into the queue.
    clicks = [
        _make_click_payload("#pricing-btn", "Pricing"),
        _make_click_payload("#cta-btn", "Get Started"),
        _make_click_payload("#confirm-btn", "Confirm"),
    ]
    for c in clicks:
        await recorder._click_queue.put(c)

    # Give the capture loop time to process all clicks + workflow dialogs.
    await asyncio.sleep(0.3)

    # Stop.
    recorder._stopped.set()
    try:
        await asyncio.wait_for(recorder._capture_task, timeout=3.0)
    except asyncio.TimeoutError:
        recorder._capture_task.cancel()

    spec = recorder.spec
    assert len(spec.steps) == 3, f"expected 3 steps, got {len(spec.steps)}"

    # Step 0.
    assert spec.steps[0].userIntent == "I want to show pricing"
    assert spec.steps[0].annotation is not None
    assert "[user intent: I want to show pricing]" in spec.steps[0].annotation

    # Step 1.
    assert spec.steps[1].userIntent == "This is the CTA"
    assert "[user intent: This is the CTA]" in (spec.steps[1].annotation or "")

    # Step 2.
    assert spec.steps[2].userIntent == "Confirmation screen"
    assert "[user intent: Confirmation screen]" in (spec.steps[2].annotation or "")

    # Verify TTS replied for each click.
    assert len(stub.reply_calls) == 3
    assert all("clicked" in c.lower() for c in stub.reply_calls)
    assert "Pricing" in stub.reply_calls[0]
    assert "Get Started" in stub.reply_calls[1]
    assert "Confirm" in stub.reply_calls[2]

    # Verify push_to_talk called with 8000ms each time.
    assert stub.push_to_talk_calls == [8000, 8000, 8000]


# ---------------------------------------------------------------------------
# Test 2: Workflow mode without voice → raises DemoRecorderError.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_workflow_mode_without_voice_raises() -> None:
    """Workflow mode requires voice_loop; raises actionable error if missing."""
    recorder = DemoRecorder(
        session_id="wf-no-voice",
        url="http://localhost:8765/test.html",
        name="No Voice",
        goal="Should fail",
        workflow_mode=True,
    )
    # voice_loop is None (default).

    with pytest.raises(DemoRecorderError, match="workflow mode requires a VoiceLoop"):
        await recorder.start()


# ---------------------------------------------------------------------------
# Test 3: DemoManager.start enforces workflow → voice requirement.
# ---------------------------------------------------------------------------

def test_demo_manager_rejects_workflow_without_voice() -> None:
    """Passing workflow=True without voice=True raises DemoRecorderError."""
    mgr = DemoManager()
    with pytest.raises(DemoRecorderError, match="workflow mode requires voice"):
        mgr.start({
            "url": "http://example.com",
            "name": "test",
            "goal": "test",
            "workflow": True,
        })


# ---------------------------------------------------------------------------
# Test 4: Empty transcript (user says nothing) — no crash, no userIntent.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_workflow_empty_transcript_graceful(tmp_path: Path) -> None:
    """User says nothing during intent prompt → step continues without userIntent."""
    stub = StubVoiceLoop(transcripts=[""])  # empty transcript

    recorder = DemoRecorder(
        session_id="wf-silent",
        url="http://localhost:8765/test.html",
        name="Silent User",
        goal="Test empty transcript",
        output_dir=tmp_path / "demos",
        workflow_mode=True,
    )
    recorder.voice_loop = stub  # type: ignore[assignment]

    mock_page = mock.AsyncMock()
    mock_page.screenshot.return_value = b"\x89PNG\r\n\x1a\n"
    mock_page.evaluate.return_value = None
    mock_page.url = "http://localhost:8765/test.html"
    recorder._page = mock_page  # type: ignore[assignment]

    recorder._started_at_ms = 1000
    recorder._capture_task = asyncio.create_task(
        recorder._capture_loop(), name="wf-silent-cap"
    )

    await recorder._click_queue.put(_make_click_payload("#btn", "Click Me"))
    await asyncio.sleep(0.3)

    recorder._stopped.set()
    try:
        await asyncio.wait_for(recorder._capture_task, timeout=3.0)
    except asyncio.TimeoutError:
        recorder._capture_task.cancel()

    assert len(recorder.spec.steps) == 1
    step = recorder.spec.steps[0]
    # Empty transcript → userIntent stays None, annotation unchanged.
    assert step.userIntent is None
    assert "[user intent:" not in (step.annotation or "")

    # TTS still fires even when there's no answer.
    assert len(stub.reply_calls) == 1


# ---------------------------------------------------------------------------
# Test 5: _prompt_step_intent directly — the pure-unit version.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_prompt_step_intent_direct() -> None:
    """Call _prompt_step_intent directly on a DemoStep → fields populated."""
    stub = StubVoiceLoop(transcripts=["Show the signup flow"])

    recorder = DemoRecorder(
        session_id="wf-unit",
        url="http://localhost:8765/test.html",
        name="Unit",
        goal="Test prompt directly",
        workflow_mode=True,
    )
    recorder.voice_loop = stub  # type: ignore[assignment]

    step = DemoStep(
        index=0,
        timestamp=500,
        pageUrl="http://localhost:8765/test.html",
        pageTitle="Test",
        interaction=Interaction(
            type="click",
            target={"selector": "#signup-btn", "tagName": "button", "text": "Sign Up Now"},
            hotspot={"xPct": 50, "yPct": 50},
        ),
    )

    await recorder._prompt_step_intent(step)

    assert step.userIntent == "Show the signup flow"
    assert step.annotation == " [user intent: Show the signup flow]"
    assert len(stub.reply_calls) == 1
    assert "Sign Up Now" in stub.reply_calls[0]


# ---------------------------------------------------------------------------
# Test 6: Voice steps (mic button) do NOT trigger workflow intent prompt.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_workflow_voice_steps_bypass_intent_prompt(tmp_path: Path) -> None:
    """Voice transcript steps (from push-to-talk mic) skip the workflow prompt."""
    stub = StubVoiceLoop(transcripts=[
        "This would be the intent if triggered",  # should never be consumed
    ])

    recorder = DemoRecorder(
        session_id="wf-voice-step",
        url="http://localhost:8765/test.html",
        name="Voice Step Test",
        goal="Voice steps should not trigger intent prompt",
        output_dir=tmp_path / "demos",
        workflow_mode=True,
    )
    recorder.voice_loop = stub  # type: ignore[assignment]

    mock_page = mock.AsyncMock()
    mock_page.screenshot.return_value = b"\x89PNG\r\n\x1a\n"
    mock_page.evaluate.return_value = None
    mock_page.url = "http://localhost:8765/test.html"
    recorder._page = mock_page  # type: ignore[assignment]

    recorder._started_at_ms = 1000
    recorder._capture_task = asyncio.create_task(
        recorder._capture_loop(), name="wf-voice-step-cap"
    )

    # Push a voice-type payload (simulating mic button release).
    await recorder._click_queue.put({
        "type": "voice",
        "transcript": "I want to highlight the hero section",
        "pageUrl": "http://localhost:8765/test.html",
        "pageTitle": "Test",
        "timestamp": 2000,
    })
    await asyncio.sleep(0.3)

    recorder._stopped.set()
    try:
        await asyncio.wait_for(recorder._capture_task, timeout=3.0)
    except asyncio.TimeoutError:
        recorder._capture_task.cancel()

    assert len(recorder.spec.steps) == 1
    # Voice step should NOT have an intent prompt.
    assert stub.push_to_talk_calls == []  # push_to_talk never called
    assert stub.reply_calls == []         # reply never called
    # Voice step has userDirection (from existing W6 logic) but NOT userIntent.
    assert recorder.spec.steps[0].userDirection == "I want to highlight the hero section"
    assert recorder.spec.steps[0].userIntent is None


# ---------------------------------------------------------------------------
# Test 7: questions stay under 15 words even with long target text.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_prompt_question_truncates_long_target() -> None:
    """Question text stays short even when the clicked element has long text."""
    stub = StubVoiceLoop(transcripts=["OK"])

    recorder = DemoRecorder(
        session_id="wf-long-text",
        url="http://localhost:8765/test.html",
        name="Long Text Test",
        goal="Question truncation",
        workflow_mode=True,
    )
    recorder.voice_loop = stub  # type: ignore[assignment]

    step = DemoStep(
        index=0,
        timestamp=500,
        pageUrl="http://localhost:8765/test.html",
        pageTitle="Test",
        interaction=Interaction(
            type="click",
            target={
                "selector": "button.big",
                "tagName": "button",
                "text": "Get Started With Our Amazing Premium Enterprise Plan Today",
            },
            hotspot={"xPct": 50, "yPct": 50},
        ),
    )

    await recorder._prompt_step_intent(step)

    question = stub.reply_calls[0]
    # Should be truncated in the question.
    assert len(question.split()) <= 15, f"question too long ({len(question.split())} words): {question!r}"
    assert "What are you illustrating" in question


# ---------------------------------------------------------------------------
# Test 8: DemoSpec round-trips userIntent through to_dict/JSON.
# ---------------------------------------------------------------------------

def test_demo_spec_user_intent_roundtrip() -> None:
    """DemoSpec.to_dict() includes userIntent; JSON round-trip preserves it."""
    from capturd.walk.schema import DemoSpec

    step = DemoStep(
        index=0,
        timestamp=100,
        pageUrl="http://example.com",
        pageTitle="Example",
        interaction=Interaction(
            type="click",
            target={"selector": "#btn", "text": "Click"},
            hotspot={"xPct": 50, "yPct": 50},
        ),
        userIntent="Demonstrate the pricing table",
    )

    spec = DemoSpec(id="wf-json", name="JSON Test", goal="Round-trip")
    spec.steps = [step]

    d = spec.to_dict()
    assert d["steps"][0]["userIntent"] == "Demonstrate the pricing table"

    # JSON round-trip.
    js = json.dumps(d)
    reloaded = json.loads(js)
    assert reloaded["steps"][0]["userIntent"] == "Demonstrate the pricing table"


# ---------------------------------------------------------------------------
# Test 9: WAV fixtures exist and are readable (owner-visible proof).
# ---------------------------------------------------------------------------

def test_fixture_wav_files_exist() -> None:
    """All 3 workflow fixture WAV files exist and are valid WAVs."""
    fixture_dir = Path(__file__).parent / "fixtures"
    for i in range(3):
        wav_path = fixture_dir / f"workflow_intent_{i}.wav"
        assert wav_path.is_file(), f"missing fixture WAV: {wav_path}"

        with wave.open(str(wav_path), "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == 16000
