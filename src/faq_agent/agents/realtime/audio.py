"""Microphone / speaker I/O for the realtime voice agent."""

from __future__ import annotations

import asyncio
import sys
from typing import Any

from agents.realtime import RealtimeSession

# Fixed by the Realtime API's default pcm16 audio format.
SAMPLE_RATE = 24_000
CHANNELS = 1
DTYPE = "int16"
BLOCKSIZE = SAMPLE_RATE // 10  # 100ms chunks


async def stream_microphone(session: RealtimeSession) -> None:
    """Captures microphone audio and streams it to the session until cancelled."""
    import sounddevice as sd

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[bytes] = asyncio.Queue()

    def on_audio(indata: bytes, _frames: int, _time_info: Any, status: sd.CallbackFlags) -> None:
        if status:
            print(f"[mic] {status}", file=sys.stderr)
        # Runs on PortAudio's own thread — hand off to the event loop instead
        # of touching the asyncio.Queue directly.
        loop.call_soon_threadsafe(queue.put_nowait, bytes(indata))

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


async def play_and_print(session: RealtimeSession) -> None:
    """Plays the agent's audio and prints each side's finished transcript to the console."""
    import sounddevice as sd

    output = sd.RawOutputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE)
    output.start()
    printed: set[str] = set()

    async for event in session:
        if event.type == "audio":
            output.write(event.audio.data)
        elif event.type == "audio_interrupted":
            # Drop whatever's still queued so playback stops as soon as the
            # caller barges in, instead of finishing the old response.
            output.stop()
            output.start()
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
