"""Realtime voice agent definition — the FAQ and reservation agents run as its tools."""

from __future__ import annotations

from agents.mcp import MCPServerStdio
from agents.realtime import RealtimeAgent

from faq_agent.agents.faq import create_faq_agent
from faq_agent.agents.reservation import create_reservation_agent
from faq_agent.config import Settings
from faq_agent.guardrails import tripwire_message

INSTRUCTIONS = (
    "Jesteś głosowym asystentem obsługi klienta linii lotniczej Example Air. "
    "Mówisz po polsku, krótko i naturalnie — to rozmowa głosowa, nie tekst.\n"
    "Sam nie znasz zasad przewozu i nie zapisujesz rezerwacji — robią to "
    "wyspecjalizowani agenci, których wywołujesz jako narzędzia:\n"
    "- ask_faq_agent — pytania o zasady przewozu, opłaty, bagaż, odprawę, "
    "zwroty i inne procedury. Przekaż pytanie pasażera własnymi słowami.\n"
    "- ask_reservation_agent — zapis rezerwacji lotu. Wywołaj go dopiero, "
    "gdy masz od pasażera imię i nazwisko, cel podróży i datę, i przekaż "
    "wszystkie trzy w jednym zapytaniu.\n"
    "Zasady:\n"
    "- Zanim wywołasz narzędzie, powiedz krótko, że sprawdzasz (np. "
    "„Chwileczkę, sprawdzam”) — odpowiedź agenta zajmuje moment.\n"
    "- Odpowiadaj wyłącznie na podstawie tego, co zwrócił agent. Nie "
    "wymyślaj cen, limitów, procedur ani numerów rezerwacji.\n"
    "- Jeśli do rezerwacji brakuje imienia i nazwiska, celu albo daty, "
    "zapytaj o to pasażera — nie zgaduj.\n"
    "- Po zapisaniu rezerwacji potwierdź ją i podaj jej numer.\n"
    "- Jeśli agent odmawia odpowiedzi, przekaż pasażerowi jego komunikat i nie "
    "ponawiaj wywołania.\n"
    "- Innych spraw indywidualnych (np. status istniejącej rezerwacji) nie "
    "obsłużysz — skieruj pasażera na infolinię."
)


def create_realtime_agent(settings: Settings, reservation_server: MCPServerStdio) -> RealtimeAgent:
    """Builds the realtime voice agent that calls the FAQ and reservation agents as tools.

    Unlike a handoff, the voice agent keeps the conversation: each sub-agent
    gets a generated question, runs as a regular text agent (`settings.model_name`)
    and returns its answer, which the voice agent then says out loud.
    """
    faq_agent = create_faq_agent(settings)
    reservation_agent = create_reservation_agent(settings, reservation_server)
    return RealtimeAgent(
        name="Voice Agent (Realtime)",
        instructions=INSTRUCTIONS,
        tools=[
            faq_agent.as_tool(
                tool_name="ask_faq_agent",
                tool_description=(
                    "Ask the FAQ agent about baggage, check-in, fees, refunds and other "
                    "airline rules and procedures. Input: the passenger's question."
                ),
                failure_error_function=tripwire_message,
            ),
            reservation_agent.as_tool(
                tool_name="ask_reservation_agent",
                tool_description=(
                    "Save a flight reservation. Input: the passenger's full name, "
                    "destination and travel date, all in one message. Returns the "
                    "reservation number."
                ),
                failure_error_function=tripwire_message,
            ),
        ],
    )
