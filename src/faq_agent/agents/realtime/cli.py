"""Command-line interface for the realtime voice agent.

Usage:
    faq-agent-realtime   # talk via microphone + speakers, Ctrl+C to stop
"""

from __future__ import annotations

import asyncio
import contextlib
import sys

from agents.realtime import RealtimeRunner

from faq_agent.agents.realtime.agent import create_realtime_agent
from faq_agent.agents.realtime.audio import play_and_print, stream_microphone
from faq_agent.agents.reservation import create_reservation_server
from faq_agent.config import Settings
from faq_agent.observability import configure_tracing


async def _amain() -> None:
    settings = Settings()
    if not settings.openai_api_key:
        sys.exit(
            "Missing API key. Set OPENAI_API_KEY in the .env file in the working directory\n"
            "(or set the OPENAI_API_KEY environment variable)."
        )
    # The sub-agents run through Runner.run, which traces on its own.
    configure_tracing(settings.openai_api_key)

    print("Example Air — realtime voice agent. Mów do mikrofonu (Ctrl+C, aby zakończyć).")
    # The reservation sub-agent's tool lives in an MCP server (a subprocess),
    # which has to stay connected for the whole session.
    async with create_reservation_server() as reservation_server:
        runner = RealtimeRunner(
            create_realtime_agent(settings, reservation_server),
            config={
                "model_settings": {
                    "model_name": settings.realtime_model_name,
                    "voice": settings.realtime_voice,
                }
            },
        )
        async with await runner.run(model_config={"api_key": settings.openai_api_key}) as session:
            mic_task = asyncio.create_task(stream_microphone(session))
            try:
                await play_and_print(session)
            finally:
                mic_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await mic_task


def main() -> None:
    try:
        asyncio.run(_amain())
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()
