"""Triage agent and its handoffs to the FAQ and reservation agents."""

from faq_agent.agents.triage.agent import create_triage_agent
from faq_agent.agents.triage.handoff import ask

__all__ = ["ask", "create_triage_agent"]
