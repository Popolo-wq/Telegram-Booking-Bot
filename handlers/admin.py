"""Admin-only commands."""

from __future__ import annotations

import html
import logging
from datetime import date

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import db

logger = logging.getLogger(__name__)
router = Router(name="admin")


@router.message(Command("admin"))
async def cmd_admin(message: Message, admin_user_id: int) -> None:
    """List today's active bookings — restricted to the configured admin.

    ``admin_user_id`` is injected from the dispatcher's workflow data
    (set in :mod:`bot`).
    """
    if message.from_user.id != admin_user_id:
        await message.answer("⛔ You are not authorized to use this command.")
        return

    today = date.today().isoformat()
    try:
        bookings = await db.get_today_bookings(today)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to load today's bookings")
        await message.answer("⚠️ Could not load bookings. Please try again later.")
        return

    if not bookings:
        await message.answer(f"📭 No bookings for today ({today}).")
        return

    lines = [f"<b>📅 Bookings for {today}</b> ({len(bookings)} total)\n"]
    for item in bookings:
        time = item["booking_datetime"][11:16]  # HH:MM
        name = html.escape(item["full_name"] or "Unknown")
        username = f"@{html.escape(item['username'])}" if item["username"] else "—"
        lines.append(
            f"🕐 <b>{time}</b> · {html.escape(item['service'])} · "
            f"{html.escape(item['master'])}\n"
            f"   👤 {name} ({username}) · "
            f"<code>BRB-{item['id']:05d}</code>\n"
        )
    await message.answer("\n".join(lines))
