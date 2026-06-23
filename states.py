"""Finite State Machine (FSM) states for the booking flow."""

from aiogram.fsm.state import State, StatesGroup


class BookingFlow(StatesGroup):
    """Steps a customer walks through when booking an appointment."""

    choosing_service = State()
    choosing_master = State()
    choosing_date = State()
    choosing_time = State()
    confirming = State()
