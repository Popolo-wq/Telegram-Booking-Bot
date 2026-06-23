"""General commands: /start, /help, /cancel and /mybookings."""

from __future__ import annotations

import html
import logging
from datetime import date, datetime

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database import db
from keyboards.inline import book_again_kb, main_menu_kb

logger = logging.getLogger(__name__)
router = Router(name="common")

WELCOME_TEXT = (
    "💈 <b>Welcome to FadeLab Barbershop!</b>\n\n"
    "Book your appointment in just a few taps — choose a service, a master, "
    "a date and a time. No calls, no waiting.\n\n"
    "Tap the button below to get started 👇"
)

HELP_TEXT = (
    "<b>FadeLab Booking Bot — commands</b>\n\n"
    "/start — open the main menu and book an appointment\n"
    "/mybookings — view your upcoming appointments\n"
    "/cancel — abort the current booking\n"
    "/help — show this message"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Greet the user, register them, and reset any in-progress flow."""
    await state.clear()
    try:
        user = message.from_user
        await db.upsert_user(user.id, user.username, user.full_name)
    except Exception:  # noqa: BLE001 - never let DB hiccups crash the greeting
        logger.exception("Failed to upsert user on /start")

    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Show the list of available commands."""
    await message.answer(HELP_TEXT)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Clear the current FSM state, if any."""
    current = await state.get_state()
    if current is None:
        await message.answer(
            "Nothing to cancel. Use /start to make another booking.",
            reply_markup=book_again_kb(),
        )
        return

    await state.clear()
    await message.answer(
        "Booking cancelled. Use /start to make another booking.",
        reply_markup=book_again_kb(),
    )


@router.message(Command("mybookings"))
async def cmd_my_bookings(message: Message) -> None:
    """List the user's upcoming active bookings."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        bookings = await db.get_user_bookings(message.from_user.id, now)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to load user bookings")
        await message.answer("⚠️ Could not load your bookings. Please try again later.")
        return

    if not bookings:
        await message.answer(
            "You have no upcoming appointments.\nSend /start to book one!"
        )
        return

    lines = ["<b>📋 Your upcoming appointments:</b>\n"]
    for item in bookings:
        when = _format_datetime(item["booking_datetime"])
        lines.append(
            f"🔖 <code>BRB-{item['id']:05d}</code>\n"
            f"   {html.escape(item['service'])} with "
            f"{html.escape(item['master'])}\n"
            f"   🗓 {when}\n"
        )
    await message.answer("\n".join(lines))


def _format_datetime(value: str) -> str:
    """Render a stored ``YYYY-MM-DD HH:MM`` string in a friendly form."""
    try:
        dt = datetime.strptime(value, "%Y-%m-%d %H:%M")
    except ValueError:
        return value
    return dt.strftime("%a, %d %b %Y · %H:%M")
