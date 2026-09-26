"""Tools exposed to the agent."""

from __future__ import annotations

from agents import function_tool

from . import knowledge_base


@function_tool
def search_faq(query: str) -> str:
    """Searches the airline FAQ knowledge base.

    Args:
        query: Keywords, e.g. "carry-on baggage dimensions"
            or "ticket refund".

    Returns:
        Matching FAQ entries, or the list of available topics when
        nothing matches.
    """
    return knowledge_base.search(query)
