"""FAQ knowledge base — in a real application this would come from a database / CMS."""

from __future__ import annotations

import unicodedata

FAQ: dict[str, str] = {
    "carry-on baggage": (
        "You may bring on board one piece of carry-on baggage up to 8 kg "
        "with maximum dimensions of 55x40x23 cm, plus one small personal "
        "item (e.g. a handbag or laptop) that fits under the seat."
    ),
    "checked baggage": (
        "The Standard fare includes one piece of checked baggage up to "
        "23 kg. Excess baggage costs PLN 50 for each started kilogram. "
        "The maximum weight of a single piece is 32 kg."
    ),
    "online check-in": (
        "Online check-in opens 48 hours before the scheduled departure "
        "and closes 2 hours before. You can keep your boarding pass in "
        "the mobile app or print it."
    ),
    "airport check-in": (
        "Check-in at an airport desk costs PLN 100. Desks close 40 "
        "minutes before departure, and gates close 20 minutes before."
    ),
    "booking changes": (
        "You can change the date or time of your flight up to 3 hours "
        "before departure, in the app or via the helpline. The fee is "
        "PLN 150 plus any difference in the ticket price."
    ),
    "ticket refund": (
        "Standard fare tickets are non-refundable — only airport fees are "
        "refunded. The Flex fare allows a full refund up to 24 hours "
        "before departure."
    ),
    "flight delay or cancellation": (
        "For a delay of more than 3 hours or a flight cancellation, you "
        "are entitled to compensation under EU Regulation 261/2004: from "
        "250 to 600 EUR depending on the route length. You can submit a "
        "claim via the form on our website under 'Complaints'."
    ),
    "traveling with a child": (
        "Children under 2 travel on a guardian's lap for 10% of the "
        "ticket price. Strollers are transported free of charge. Children "
        "aged 5 to 12 may fly alone with the assistance service "
        "(PLN 300 fee)."
    ),
    "pets on board": (
        "Small pets (up to 8 kg including the carrier) may travel in the "
        "cabin for a PLN 250 fee. Larger animals are transported in the "
        "cargo hold. Advance booking via the helpline is required."
    ),
    "helpline contact": (
        "Helpline: +48 22 123 45 67, daily 7:00–22:00. "
        "E-mail: support@example-air.com. The passenger service desk at "
        "the airport can also help."
    ),
}


def _normalize(text: str) -> str:
    """Lowercases text and strips diacritical marks (including Polish 'ł')."""
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in text if not unicodedata.combining(char)).replace("ł", "l")


def search(query: str) -> str:
    """Returns FAQ entries matching the keywords in the query.

    When nothing matches, returns the list of available topics.
    """
    words = {w for w in _normalize(query).split() if len(w) > 2}
    matches: list[str] = []
    for topic, content in FAQ.items():
        entry_text = _normalize(f"{topic} {content}")
        if any(word in entry_text for word in words):
            matches.append(f"[{topic}] {content}")

    if matches:
        return "\n\n".join(matches)
    return (
        "No direct matches. Available FAQ topics: "
        + ", ".join(FAQ) + "."
    )
