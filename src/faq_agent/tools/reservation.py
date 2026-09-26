"""Reservation MCP server (stdio) — saves what the passenger tells us to a JSON Lines file.

Not imported by the agents: the reservation agent starts it as a subprocess
through `MCPServerStdio` (see `agents/reservation/agent.py`). Run it by hand
with `python tools/reservation.py` to inspect it with any MCP client.
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp.server.mcpserver import MCPServer

RESERVATIONS_FILE = Path("reservations.jsonl")

mcp = MCPServer("Reservations")


@mcp.tool()
def save_reservation(passenger_name: str, destination: str, date: str) -> str:
    """Saves a flight reservation requested by the passenger.

    Args:
        passenger_name: First and last name of the passenger.
        destination: Destination city or airport, e.g. "Londyn".
        date: Travel date as given by the passenger, e.g. "2026-10-12".

    Returns:
        Confirmation with the reservation number.
    """
    saved = RESERVATIONS_FILE.read_text().splitlines() if RESERVATIONS_FILE.exists() else []
    number = f"RES-{len(saved) + 1:04d}"
    record = {
        "number": number,
        "passenger_name": passenger_name,
        "destination": destination,
        "date": date,
    }
    with RESERVATIONS_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
    return f"Reservation saved. Number: {number}."


if __name__ == "__main__":
    mcp.run()
