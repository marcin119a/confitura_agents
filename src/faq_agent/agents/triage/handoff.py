"""Agent hand-off, using the SDK's native `handoffs=` mechanism.

The triage agent doesn't answer on its own: it calls a handoff tool
(`transfer_to_faq_agent` or `transfer_to_reservation_agent`) and the chosen
agent takes over the conversation and writes the final answer. The whole
chain is a single `Runner.run`, so the SDK puts every step into one trace —
the run shows up as one workflow at platform.openai.com/traces.

Routing is decided by the LLM from the handoff descriptions, which is the
trade-off of this approach (compared to a deterministic if/else on a
structured triage result).

The reservation agent's tool lives in an MCP server (a subprocess), which
has to be connected for the duration of the run — hence the `async with`.
"""

from __future__ import annotations

import asyncio

from agents import (
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    RunConfig,
    Runner,
)

from faq_agent.agents.reservation import create_reservation_server
from faq_agent.agents.triage.agent import create_triage_agent
from faq_agent.config import Settings
from faq_agent.observability import configure_tracing


async def _run(question: str, settings: Settings) -> str:
    async with create_reservation_server() as reservation_server:
        try:
            result = await Runner.run(
                create_triage_agent(settings, reservation_server),
                question,
                run_config=RunConfig(workflow_name="Handoff Workflow"),
            )
        except InputGuardrailTripwireTriggered:
            return ""
        except OutputGuardrailTripwireTriggered:
            return ""
    return result.final_output


def ask(question: str, settings: Settings | None = None) -> str:
    """Runs the triage agent, which hands off to the FAQ or reservation agent, and returns the answer."""
    settings = settings or Settings()
    configure_tracing(settings.openai_api_key)
    return asyncio.run(_run(question, settings))
