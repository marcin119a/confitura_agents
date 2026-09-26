"""Tracing setup for the FAQ agent.

The OpenAI Agents SDK traces every run automatically — no separate service
or account to set up, unlike Agno (AgentOS) or Pydantic AI (Logfire).
Traces show up at https://platform.openai.com/traces under your OpenAI
account. The exporter authenticates with the same OpenAI API key as the
model calls; since Settings loads it from .env without exporting it to
os.environ, it has to be handed to the exporter explicitly.
"""

from __future__ import annotations

from agents import set_tracing_export_api_key


def configure_tracing(api_key: str) -> None:
    """Points the built-in trace exporter at the configured OpenAI account."""
    if api_key:
        set_tracing_export_api_key(api_key)
