"""Microphone / speaker I/O for the realtime voice agent."""

from __future__ import annotations

import asyncio
import sys
import time
from typing import Any

from agents.realtime import RealtimeSession

# Fixed by the Realtime API's default pcm16 audio format.
SAMPLE_RATE = 24_000
CHANNELS = 1
DTYPE = "int16"
BLOCKSIZE = SAMPLE_RATE // 10  # 100ms chunks
BYTES_PER_SECOND = SAMPLE_RATE * CHANNELS * 2  # int16

# How long the room keeps echoing the agent's voice after the last sample played.
ECHO_TAIL_S = 0.4


class EchoGate:
    """Tells whether the microphone may be listened to right now.

    With speakers (not headphones) the microphone picks up the agent's own
    voice, the server's VAD takes it for the caller and the agent ends up
    answering itself. So the microphone stays muted while the agent is
    audible, plus a short echo tail. The price: no barge-in over the agent's
    voice.
    """

    def __init__(self) -> None:
        self._playback_end = 0.0

    def played(self, audio: bytes) -> None:
        """Registers audio that is about to be played; call it before writing it out."""
        start = max(self._playback_end, time.monotonic())
        self._playback_end = start + len(audio) / BYTES_PER_SECOND

    def flushed(self) -> None:
        """Registers that the playback queue was dropped."""
        self._playback_end = time.monotonic()

    @property
    def is_open(self) -> bool:
        return time.monotonic() >= self._playback_end + ECHO_TAIL_S


async def stream_microphone(session: RealtimeSession, gate: EchoGate) -> None:
    """Captures microphone audio and streams it to the session until cancelled.

    While the gate is closed the session gets silence instead of the captured
    audio, so the server's VAD keeps a continuous timeline but hears no echo.
    """
    import sounddevice as sd

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[bytes] = asyncio.Queue()

    def on_audio(indata: bytes, _frames: int, _time_info: Any, status: sd.CallbackFlags) -> None:
        if status:
            print(f"[mic] {status}", file=sys.stderr)
        # Decide here, at capture time — chunks can wait in the queue while the
        # event loop is busy writing to the speakers.
        chunk = bytes(indata) if gate.is_open else bytes(len(indata))
        # Runs on PortAudio's own thread — hand off to the event loop instead
        # of touching the asyncio.Queue directly.
        loop.call_soon_threadsafe(queue.put_nowait, chunk)

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=DTYPE,
        blocksize=BLOCKSIZE,
        callback=on_audio,
    ):
        while True:
            chunk = await queue.get()
            await session.send_audio(chunk)


def _transcript_text(item: Any) -> str | None:
    if getattr(item, "type", None) != "message":
        return None
    for content in item.content:
        transcript = getattr(content, "transcript", None) or getattr(content, "text", None)
        if transcript:
            return transcript
    return None


async def play_and_print(session: RealtimeSession, gate: EchoGate) -> None:
    """Plays the agent's audio and prints each side's finished transcript to the console.

    Reports the played audio to the gate, which mutes the microphone meanwhile.
    """
    import sounddevice as sd

    output = sd.RawOutputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE)
    output.start()
    printed: set[str] = set()

    async for event in session:
        if event.type == "audio":
            # Before the (blocking) write, so the mic is already muted while it plays.
            gate.played(event.audio.data)
            output.write(event.audio.data)
        elif event.type == "audio_interrupted":
            # Drop whatever's still queued so playback stops as soon as the
            # caller barges in, instead of finishing the old response.
            output.stop()
            output.start()
            gate.flushed()
        elif event.type == "tool_start":
            print(f"\n[tool] {event.tool.name}({' '.join(event.arguments.split())})")
        elif event.type == "tool_end":
            print(f"[tool] {event.tool.name} -> {event.output}")
        elif event.type == "history_updated":
            for item in event.history:
                if item.item_id in printed:
                    continue
                if (
                    item.type == "message"
                    and item.role == "assistant"
                    and item.status != "completed"
                ):
                    continue  # still generating; wait for the final transcript
                text = _transcript_text(item)
                if not text:
                    continue
                label = "Ty" if getattr(item, "role", None) == "user" else "Agent"
                print(f"\n{label}: {text}")
                printed.add(item.item_id)
        elif event.type == "error":
            print(f"\n[error] {event.error}", file=sys.stderr)
