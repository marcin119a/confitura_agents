"""Command-line interface for the FAQ agent.

Usage:
    faq-agent                  # interactive mode (conversation)
    faq-agent "your question"  # single question
    python -m faq_agent        # equivalent to faq-agent
"""

from __future__ import annotations

import sys
from uuid import uuid4

from agents import (
    Agent,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    Runner,
    SQLiteSession,
)

from faq_agent.agents.faq.agent import create_faq_agent
from faq_agent.config import Settings
from faq_agent.observability import configure_tracing


def _answer(agent: Agent, question: str, session: SQLiteSession | None = None) -> str:
    """Runs the agent; a guardrail tripwire turns into a fixed message."""
    return Runner.run_sync(agent, question, session=session).final_output


def main() -> None:
    settings = Settings()
    if not settings.openai_api_key:
        sys.exit(
            "Missing API key. Set OPENAI_API_KEY in the .env file in the working directory\n"
            "(or set the OPENAI_API_KEY environment variable)."
        )

    configure_tracing(settings.openai_api_key)
    agent = create_faq_agent(settings)

    if len(sys.argv) > 1:
        # One-shot mode: question passed as an argument.
        print(_answer(agent, " ".join(sys.argv[1:])))
        return

    print("Example Air airline FAQ agent (type 'exit' to quit)")
    session = SQLiteSession(str(uuid4()))  # in-memory; not persisted between runs
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            break
        print(f"\nAgent: {_answer(agent, question, session)}")
