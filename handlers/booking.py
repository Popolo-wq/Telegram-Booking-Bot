"""The 4-step booking flow, driven by the :class:`BookingFlow` FSM.

Each step has a small ``_render_*`` helper so that both forward navigation
(choosing an option) and backward navigation (the ⬅️ Back button) reuse the
exact same rendering logic.
"""

from __future__ import annotations

import html
import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from config import SERVICES, TIME_SLOTS
from database import db
from handlers.common import WELCOME_TEXT
from keyboards.inline import (
    NAV_DATE,
    NAV_MASTER,
    NAV_MENU,
    NAV_SERVICE,
    NAV_TIME,
    START_BOOKING,
    ConfirmCB,
    DateCB,
    MasterCB,
    ServiceCB,
    TimeCB,
    book_again_kb,
    confirm_kb,
    dates_kb,
    main_menu_kb,
    masters_kb,
    services_kb,
    times_kb,
)
from states import BookingFlow

logger = logging.getLogger(__name__)
router = Router(name="booking")


# --- Step renderers ----------------------------------------------------------


async def _render_services(callback: CallbackQuery, state: FSMContext) -> None:
    """Step 1 — choose a service."""
    await state.set_state(BookingFlow.choosing_service)
    await callback.message.edit_text(
        "<b>Step 1 of 4 — choose a service:</b>", reply_markup=services_kb()
    )


async def _render_masters(callback: CallbackQuery, state: FSMContext) -> None:
    """Step 2 — choose a master."""
    data = await state.get_data()
    service = SERVICES[data["service_key"]]
    await state.set_state(BookingFlow.choosing_master)
    await callback.message.edit_text(
        f"Service: <b>{service['title']}</b> (${service['price']})\n\n"
        "<b>Step 2 of 4 — choose your master:</b>",
        reply_markup=masters_kb(),
    )


async def _render_dates(callback: CallbackQuery, state: FSMContext) -> None:
    """Step 3 — choose a date."""
    data = await state.get_data()
    await state.set_state(BookingFlow.choosing_date)
    await callback.message.edit_text(
        f"Master: <b>{html.escape(data['master'])}</b>\n\n"
        "<b>Step 3 of 4 — choose a date:</b>",
        reply_markup=dates_kb(),
    )


async def _render_times(callback: CallbackQuery, state: FSMContext) -> bool:
    """Step 4 — choose a time. Returns ``False`` if the day is fully booked."""
    data = await state.get_data()
    master, date_iso = data["master"], data["date_iso"]

    taken = await db.get_taken_slots(master, date_iso)
    available = [slot for slot in TIME_SLOTS if slot not in taken]
    if not available:
        await callback.message.edit_text(
            "😔 No free slots on that day. Please pick another date:",
            reply_markup=dates_kb(),
        )
        await state.set_state(BookingFlow.choosing_date)
        return False

    await state.set_state(BookingFlow.choosing_time)
    await callback.message.edit_text(
        f"Date: <b>{_format_date(date_iso)}</b>\n\n"
        "<b>Step 4 of 4 — choose a time:</b>",
        reply_markup=times_kb(available),
    )
    return True


# --- Forward navigation ------------------------------------------------------


@router.callback_query(F.data == START_BOOKING)
async def start_booking(callback: CallbackQuery, state: FSMContext) -> None:
    """Entry point — Step 1: choose a service."""
    await state.clear()
    await _render_services(callback, state)
    await callback.answer()


@router.callback_query(BookingFlow.choosing_service, ServiceCB.filter())
async def choose_service(
    callback: CallbackQuery, callback_data: ServiceCB, state: FSMContext
) -> None:
    """Store the service and move to Step 2: choose a master."""
    if callback_data.key not in SERVICES:
        await callback.answer("Unknown service, please /start again.", show_alert=True)
        return

    await state.update_data(service_key=callback_data.key)
    await _render_masters(callback, state)
    await callback.answer()


@router.callback_query(BookingFlow.choosing_master, MasterCB.filter())
async def choose_master(
    callback: CallbackQuery, callback_data: MasterCB, state: FSMContext
) -> None:
    """Store the master and move to Step 3: choose a date."""
    await state.update_data(master=callback_data.name)
    await _render_dates(callback, state)
    await callback.answer()


@router.callback_query(BookingFlow.choosing_date, DateCB.filter())
async def choose_date(
    callback: CallbackQuery, callback_data: DateCB, state: FSMContext
) -> None:
    """Store the date and move to Step 4: choose a time."""
    await state.update_data(date_iso=callback_data.iso)
    try:
        await _render_times(callback, state)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to render time slots")
        await callback.answer("⚠️ Something went wrong. Try again.", show_alert=True)
        return
    await callback.answer()


@router.callback_query(BookingFlow.choosing_time, TimeCB.filter())
async def choose_time(
    callback: CallbackQuery, callback_data: TimeCB, state: FSMContext
) -> None:
    """Store the time and show the confirmation screen."""
    await state.update_data(time=callback_data.slot)
    data = await state.get_data()
    service = SERVICES[data["service_key"]]

    summary = (
        "<b>Please confirm your booking:</b>\n\n"
        f"💈 Service: <b>{service['title']}</b> (${service['price']})\n"
        f"✂️ Master: <b>{html.escape(data['master'])}</b>\n"
        f"🗓 Date: <b>{_format_date(data['date_iso'])}</b>\n"
        f"🕐 Time: <b>{callback_data.slot}</b>"
    )

    await state.set_state(BookingFlow.confirming)
    await callback.message.edit_text(summary, reply_markup=confirm_kb())
    await callback.answer()


# --- Backward navigation (⬅️ Back) -------------------------------------------


@router.callback_query(F.data == NAV_MENU)
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Return to the welcome screen and reset the flow."""
    await state.clear()
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == NAV_SERVICE)
async def back_to_service(callback: CallbackQuery, state: FSMContext) -> None:
    """Go back to Step 1."""
    await _render_services(callback, state)
    await callback.answer()


@router.callback_query(F.data == NAV_MASTER)
async def back_to_master(callback: CallbackQuery, state: FSMContext) -> None:
    """Go back to Step 2."""
    await _render_masters(callback, state)
    await callback.answer()


@router.callback_query(F.data == NAV_DATE)
async def back_to_date(callback: CallbackQuery, state: FSMContext) -> None:
    """Go back to Step 3."""
    await _render_dates(callback, state)
    await callback.answer()


@router.callback_query(F.data == NAV_TIME)
async def back_to_time(callback: CallbackQuery, state: FSMContext) -> None:
    """Go back to Step 4 (recomputing free slots)."""
    try:
        await _render_times(callback, state)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to render time slots")
        await callback.answer("⚠️ Something went wrong. Try again.", show_alert=True)
        return
    await callback.answer()


# --- Confirmation ------------------------------------------------------------


@router.callback_query(BookingFlow.confirming, ConfirmCB.filter())
async def confirm_booking(
    callback: CallbackQuery, callback_data: ConfirmCB, state: FSMContext
) -> None:
    """Persist the booking (or cancel) and finish the flow."""
    if callback_data.action == "cancel":
        await state.clear()
        await callback.message.edit_text(
            "Booking cancelled. Use /start to make another booking.",
            reply_markup=book_again_kb(),
        )
        await callback.answer()
        return

    data = await state.get_data()
    service = SERVICES[data["service_key"]]
    booking_datetime = f"{data['date_iso']} {data['time']}"

    try:
        user = callback.from_user
        user_id = await db.upsert_user(user.id, user.username, user.full_name)
        booking_id = await db.create_booking(
            user_id, str(service["title"]), data["master"], booking_datetime
        )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to create booking")
        await callback.message.edit_text(
            "⚠️ Something went wrong while saving your booking. "
            "Use /start to try again.",
            reply_markup=book_again_kb(),
        )
        await state.clear()
        await callback.answer()
        return

    if booking_id is None:
        await callback.message.edit_text(
            "😔 Sorry, that slot was just taken by someone else.\n"
            "Use /start to pick another time.",
            reply_markup=book_again_kb(),
        )
    else:
        code = f"BRB-{booking_id:05d}"
        await callback.message.edit_text(
            "✅ <b>Booking confirmed!</b>\n\n"
            f"🔖 Booking ID: <code>{code}</code>\n"
            f"💈 Service: <b>{service['title']}</b> (${service['price']})\n"
            f"✂️ Master: <b>{html.escape(data['master'])}</b>\n"
            f"🗓 Date: <b>{_format_date(data['date_iso'])}</b>\n"
            f"🕐 Time: <b>{data['time']}</b>\n\n"
            "See you at FadeLab! Use /start to make another booking.",
            reply_markup=book_again_kb(),
        )

    await state.clear()
    await callback.answer()


def _format_date(iso: str) -> str:
    """Render an ISO date (YYYY-MM-DD) as e.g. ``Tue, 23 Jun 2026``."""
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%a, %d %b %Y")
    except ValueError:
        return iso
