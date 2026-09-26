"""Triage agent definition — it hands the question off to the FAQ or reservation agent."""

from __future__ import annotations

from agents import Agent, AsyncOpenAI, OpenAIResponsesModel
from agents.mcp import MCPServerStdio

from faq_agent.agents.faq import create_faq_agent
from faq_agent.agents.reservation import create_reservation_agent
from faq_agent.config import Settings

TRIAGE_INSTRUCTIONS = (
    "Jesteś agentem triażu obsługi klienta linii lotniczej Example Air.\n"
    "Nie odpowiadasz na pytania sam — przekaż pasażera jednemu z agentów:\n"
    "- Agent rezerwacji — pasażer chce zarezerwować lot i podaje swoje dane.\n"
    "- Agent FAQ — wszystkie pozostałe pytania (zasady, opłaty, procedury, "
    "bagaż, odprawa, zwroty itp.)."
)


def create_triage_agent(settings: Settings, reservation_server: MCPServerStdio) -> Agent:
    """Builds the triage agent with handoffs to the FAQ and reservation agents."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    return Agent(
        name="Triage Agent",
        instructions=TRIAGE_INSTRUCTIONS,
        model=OpenAIResponsesModel(model=settings.model_name, openai_client=client),
        handoffs=[
            create_faq_agent(settings),
            create_reservation_agent(settings, reservation_server),
        ],
    )
