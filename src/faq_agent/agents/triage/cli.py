"""Command-line interface for the triage hand-off.

Usage:
    faq-agent-handoff "your question"
"""

from __future__ import annotations

import sys

from faq_agent.agents.triage.handoff import ask


def main() -> None:
    question = " ".join(sys.argv[1:]) or "Ile kosztuje nadbagaż?"
    print(ask(question))


if __name__ == "__main__":
    main()
