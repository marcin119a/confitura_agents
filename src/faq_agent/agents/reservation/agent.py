"""Reservation agent definition — its tool comes from an MCP server."""

from __future__ import annotations

import sys
from pathlib import Path

from agents import Agent, AsyncOpenAI, OpenAIResponsesModel
from agents.mcp import MCPServerStdio

from faq_agent.config import Settings

# tools/reservation.py, started as a subprocess that talks MCP over stdio.
RESERVATION_SERVER = Path(__file__).resolve().parents[2] / "tools" / "reservation.py"

INSTRUCTIONS = (
    "Jesteś asystentem rezerwacji linii lotniczej Example Air. "
    "Odpowiadasz po polsku, krótko i uprzejmie.\n"
    "Zasady:\n"
    "- Zapisujesz rezerwację na podstawie danych od pasażera: imię i "
    "nazwisko, cel podróży i data.\n"
    "- Zapisz ją narzędziem save_reservation, gdy tylko masz wszystkie trzy "
    "dane. Nie pytaj o nic więcej. Niczego nie wymyślaj — jeśli którejś z "
    "trzech danych brakuje, zapytaj o nią pasażera.\n"
    "- Po zapisaniu potwierdź rezerwację i podaj jej numer."
)


def create_reservation_server() -> MCPServerStdio:
    """Builds the client of the reservation MCP server.

    The server process starts on `async with`, so it has to be entered
    before any agent that uses it runs.
    """
    return MCPServerStdio(
        name="Reservations",
        params={"command": sys.executable, "args": [str(RESERVATION_SERVER)]},
        cache_tools_list=True,
    )


def create_reservation_agent(settings: Settings, server: MCPServerStdio) -> Agent:
    """Builds the reservation agent with the tools of the given MCP server."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    return Agent(
        name="Reservation Agent",
        handoff_description="Zapisywanie rezerwacji lotu na podstawie danych od pasażera.",
        instructions=INSTRUCTIONS,
        model=OpenAIResponsesModel(model=settings.model_name, openai_client=client),
        mcp_servers=[server],
    )
