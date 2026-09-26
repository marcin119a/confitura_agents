

from __future__ import annotations

import re
from typing import Any

from agents import (
    Agent,
    AsyncOpenAI,
    GuardrailFunctionOutput,
    InputGuardrail,
    InputGuardrailTripwireTriggered,
    OpenAIResponsesModel,
    OutputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    default_tool_error_function,
    input_guardrail,
    output_guardrail,
)
from pydantic import BaseModel

from faq_agent.config import Settings

INPUT_BLOCKED = (
    "Odpowiadam tylko na pytania o obsługę klienta Example Air: bagaż, odprawę, rezerwacje i opłaty."
)
OUTPUT_BLOCKED = "Nie mogę podać tej odpowiedzi. Skontaktuj się z infolinią."

OFF_TOPIC_INSTRUCTIONS = (
    "Oceniasz wiadomość pasażera linii lotniczej Example Air. Ustaw is_off_topic=true "
    "tylko wtedy, gdy wiadomość ewidentnie nie ma nic wspólnego z linią lotniczą, "
    "np. pytanie o przepis kulinarny, o politykę albo prośba o napisanie kodu.\n"
    "Na temat (is_off_topic=false) są: bagaż, odprawa, bilety, opłaty, zwroty, infolinia "
    "oraz rezerwacja lotu — także wtedy, gdy pasażer podaje samo imię i nazwisko, cel "
    "podróży i datę, np. 'Zarezerwuj lot do Londynu na 2026-10-12 dla Jana Kowalskiego'.\n"
    "Powitania, podziękowania i krótkie pytania uzupełniające (np. 'a dla dziecka?') "
    "są na temat. W razie wątpliwości ustaw is_off_topic=false."
)

# 13-19 digits, optionally separated by spaces or dashes — the length of a card number.
CARD_NUMBER = re.compile(r"\b(?:\d[ -]?){13,19}\b")


class OffTopicCheck(BaseModel):
    is_off_topic: bool


def create_off_topic_guardrail(settings: Settings) -> InputGuardrail:
    """Builds the input guardrail that blocks questions unrelated to the airline."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    classifier = Agent(
        name="Off-topic classifier",
        instructions=OFF_TOPIC_INSTRUCTIONS,
        model=OpenAIResponsesModel(model=settings.model_name, openai_client=client),
        output_type=OffTopicCheck,
    )

    @input_guardrail
    async def off_topic(
        context: RunContextWrapper[Any], agent: Agent[Any], user_input: Any
    ) -> GuardrailFunctionOutput:
        result = await Runner.run(classifier, user_input, context=context.context)
        return GuardrailFunctionOutput(
            output_info=result.final_output,
            tripwire_triggered=result.final_output.is_off_topic,
        )

    return off_topic


@output_guardrail
def no_card_number(
    context: RunContextWrapper[Any], agent: Agent[Any], output: str
) -> GuardrailFunctionOutput:
    """Output guardrail: the answer must not contain a payment card number."""
    found = CARD_NUMBER.search(output) is not None
    return GuardrailFunctionOutput(
        output_info={"card_number_found": found},
        tripwire_triggered=found,
    )


def tripwire_message(context: RunContextWrapper[Any], error: Exception) -> str:
    """Tool error function: a guardrail tripwire becomes the fixed message, like in the CLIs.

    Run as a tool (`Agent.as_tool`), a sub-agent is the first agent of its own
    run, so its guardrails do fire — and the SDK would otherwise hand the model
    a generic "an error occurred, please try again".
    """
    if isinstance(error, InputGuardrailTripwireTriggered):
        return INPUT_BLOCKED
    if isinstance(error, OutputGuardrailTripwireTriggered):
        return OUTPUT_BLOCKED
    return default_tool_error_function(context, error)
