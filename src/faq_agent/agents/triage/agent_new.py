from __future__ import annotations

from agents import Agent, AsyncOpenAI, OpenAIResponsesModel
from faq_agent.guardrails import create_off_topic_guardrail
from agents.mcp import MCPServerStdio

from faq_agent.agents.faq import create_faq_agent
from faq_agent.agents.reservation import create_reservation_agent, tripwire_message
from faq_agent.config import Settings

TRIAGE_INSTRUCTIONS = (
    "Jesteś asystentem obsługi klienta linii lotniczej Example Air. "
    "Odpowiadasz po polsku, krótko i uprzejmie, jedną wiadomością.\n"
    "Sam nie znasz zasad przewozu i nie zapisujesz rezerwacji — robią to "
    "wyspecjalizowani agenci, których wywołujesz jako narzędzia:\n"
    "- ask_faq_agent — pytania o zasady, opłaty, procedury, bagaż, odprawę, "
    "zwroty itp. Przekaż pytanie pasażera własnymi słowami.\n"
    "- ask_reservation_agent — zapis rezerwacji lotu. Przekaż imię i "
    "nazwisko, cel podróży i datę w jednym zapytaniu.\n"
    "Zasady:\n"
    "- Jeśli wiadomość zawiera obie sprawy (np. pytanie o bagaż i prośbę o "
    "rezerwację), wywołaj oba narzędzia naraz, w jednej turze — nie czekaj "
    "na wynik jednego, żeby wywołać drugie.\n"
    "- Odpowiadaj wyłącznie na podstawie tego, co zwróciły narzędzia. Nie "
    "wymyślaj cen, limitów, procedur ani numerów rezerwacji.\n"
    "- Jeśli do rezerwacji brakuje imienia i nazwiska, celu albo daty, nie "
    "wywołuj ask_reservation_agent — zapytaj o to pasażera.\n"
    "- Jeśli narzędzie odmawia odpowiedzi, przekaż pasażerowi jego komunikat "
    "i nie ponawiaj wywołania."
)


def create_triage_agent(settings: Settings, reservation_server: MCPServerStdio) -> Agent:
    """Builds the triage agent that calls the FAQ and reservation agents as tools.
    """
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    faq_agent = create_faq_agent(settings)
    reservation_agent = create_reservation_agent(settings, reservation_server)
    return Agent(
        name="Triage Agent",
        instructions=TRIAGE_INSTRUCTIONS,
        model=OpenAIResponsesModel(model=settings.model_name, openai_client=client),
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
        input_guardrails=[
            create_off_topic_guardrail(settings),
        ]
    )
