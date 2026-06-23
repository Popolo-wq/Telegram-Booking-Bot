"""Inline keyboard builders and typed callback-data factories.

Using :class:`~aiogram.filters.callback_data.CallbackData` factories instead of
raw strings keeps callbacks type-safe and self-documenting, and lets handlers
filter on them declaratively.

Plain-string callbacks (``start_booking`` and the ``nav_*`` family) are used for
navigation between steps, where there is no payload to carry.
"""

from __future__ import annotations

from datetime import date, timedelta

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import MASTERS, SERVICES

# --- Navigation callbacks ----------------------------------------------------

NAV_MENU = "nav_menu"
NAV_SERVICE = "nav_service"
NAV_MASTER = "nav_master"
NAV_DATE = "nav_date"
NAV_TIME = "nav_time"
START_BOOKING = "start_booking"


# --- Callback-data factories -------------------------------------------------


class ServiceCB(CallbackData, prefix="svc"):
    """Carries the chosen service key."""

    key: str


class MasterCB(CallbackData, prefix="mst"):
    """Carries the chosen master's name."""

    name: str


class DateCB(CallbackData, prefix="date"):
    """Carries the chosen date as an ISO string (YYYY-MM-DD)."""

    iso: str


class TimeCB(CallbackData, prefix="time"):
    """Carries the chosen time slot (HH:MM)."""

    slot: str


class ConfirmCB(CallbackData, prefix="cf"):
    """Carries the final action: ``confirm`` or ``cancel``."""

    action: str


# --- Keyboards ---------------------------------------------------------------


def main_menu_kb() -> InlineKeyboardMarkup:
    """Welcome screen with a single call-to-action."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Book appointment", callback_data=START_BOOKING)
    return builder.as_markup()


def services_kb() -> InlineKeyboardMarkup:
    """Step 1 — list of services with prices."""
    builder = InlineKeyboardBuilder()
    for key, service in SERVICES.items():
        builder.button(
            text=f"{service['title']} — ${service['price']}",
            callback_data=ServiceCB(key=key),
        )
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Back", callback_data=NAV_MENU))
    return builder.as_markup()


def masters_kb() -> InlineKeyboardMarkup:
    """Step 2 — list of available masters."""
    builder = InlineKeyboardBuilder()
    for name in MASTERS:
        builder.button(text=name, callback_data=MasterCB(name=name))
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Back", callback_data=NAV_SERVICE))
    return builder.as_markup()


def dates_kb() -> InlineKeyboardMarkup:
    """Step 3 — today, tomorrow and the day after."""
    builder = InlineKeyboardBuilder()
    today = date.today()
    labels = ["Today", "Tomorrow", "Day after tomorrow"]
    for offset, label in enumerate(labels):
        day = today + timedelta(days=offset)
        builder.button(
            text=f"{label} · {day.strftime('%d %b')}",
            callback_data=DateCB(iso=day.isoformat()),
        )
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Back", callback_data=NAV_MASTER))
    return builder.as_markup()


def times_kb(available_slots: list[str]) -> InlineKeyboardMarkup:
    """Step 4 — only the time slots that are still free."""
    builder = InlineKeyboardBuilder()
    for slot in available_slots:
        builder.button(text=slot, callback_data=TimeCB(slot=slot))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="⬅️ Back", callback_data=NAV_DATE))
    return builder.as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    """Step 5 — final confirmation, with a way back to time selection."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Confirm", callback_data=ConfirmCB(action="confirm"))
    builder.button(text="❌ Cancel", callback_data=ConfirmCB(action="cancel"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="⬅️ Back", callback_data=NAV_TIME))
    return builder.as_markup()


def book_again_kb() -> InlineKeyboardMarkup:
    """Shown after a booking finishes or is cancelled."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Book again", callback_data=START_BOOKING)
    return builder.as_markup()
