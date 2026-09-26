"""Command-line interface for the triage hand-off.

Usage:
    faq-agent-handoff                  # interactive mode (conversation)
    faq-agent-handoff "your question"  # single question
"""

from __future__ import annotations

import sys
from uuid import uuid4

from agents import SQLiteSession

from faq_agent.agents.triage.handoff import ask
from faq_agent.config import Settings


def main() -> None:
    settings = Settings()

    if len(sys.argv) > 1:
        # One-shot mode: question passed as an argument.
        print(ask(" ".join(sys.argv[1:]), settings))
        return

    print("Example Air airline assistant (type 'exit' to quit)")
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
        print(f"\nAgent: {ask(question, settings, session)}")


if __name__ == "__main__":
    main()
