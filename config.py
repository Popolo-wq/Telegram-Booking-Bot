"""Application configuration and the service catalog.

Environment variables are loaded from a local ``.env`` file (see ``.env.example``).
The catalog constants (services, masters, time slots) live here so that handlers
and keyboards share a single source of truth.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    """Strongly-typed application settings."""

    bot_token: str
    admin_user_id: int


def load_config() -> Config:
    """Read settings from the environment.

    Raises:
        RuntimeError: if ``BOT_TOKEN`` is missing — the bot cannot start without it.
    """
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "BOT_TOKEN is not set. Copy .env.example to .env and fill it in."
        )

    admin_raw = os.getenv("ADMIN_USER_ID", "0")
    try:
        admin_user_id = int(admin_raw)
    except ValueError as exc:
        raise RuntimeError("ADMIN_USER_ID must be an integer.") from exc

    return Config(bot_token=token, admin_user_id=admin_user_id)


# --- Service catalog ---------------------------------------------------------
# A single source of truth shared by keyboards and handlers.

SERVICES: dict[str, dict[str, object]] = {
    "haircut": {"title": "Haircut", "price": 20},
    "beard": {"title": "Beard trim", "price": 15},
    "haircut_beard": {"title": "Haircut + Beard", "price": 30},
    "kids": {"title": "Kids haircut", "price": 15},
}

MASTERS: list[str] = ["Aldiyar", "Yerlan", "Bauyrzhan"]

TIME_SLOTS: list[str] = ["10:00", "11:30", "13:00", "14:30", "16:00", "17:30"]
