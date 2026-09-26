from __future__ import annotations

from agents import Agent, AsyncOpenAI, OpenAIResponsesModel

from faq_agent.config import Settings
from faq_agent.guardrails import create_off_topic_guardrail, no_card_number
from faq_agent.tools import search_faq

INSTRUCTIONS = (
    "Jesteś asystentem obsługi klienta linii lotniczej Example Air. "
    "Odpowiadasz po polsku, krótko i uprzejmie.\n"
    "Zasady:\n"
    "- Zanim odpowiesz na pytanie o zasady przewozu, opłaty czy procedury, "
    "zawsze sprawdź bazę FAQ narzędziem search_faq.\n"
    "- Baza FAQ jest po angielsku — szukaj angielskich słów kluczowych, "
    "a pasażerowi odpowiadaj po polsku.\n"
    "- Odpowiadaj wyłącznie na podstawie informacji z FAQ. Nie wymyślaj "
    "cen, limitów ani procedur, których tam nie ma.\n"
    "- Jeśli FAQ nie zawiera odpowiedzi, powiedz to wprost i skieruj "
    "pasażera na infolinię (temat 'helpline contact').\n"
    "- Nie masz dostępu do rezerwacji pasażerów — sprawy indywidualne "
    "(np. status konkretnego lotu) kieruj na infolinię."
)


def create_faq_agent(settings: Settings) -> Agent:
    """Builds the FAQ agent with the configured model and tools."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    return Agent(
        name="FAQ Agent",
        handoff_description="Pytania o zasady przewozu, opłaty i procedury — odpowiedzi z bazy FAQ.",
        instructions=INSTRUCTIONS,
        model=OpenAIResponsesModel(model=settings.model_name, openai_client=client),
        tools=[search_faq],
    )
