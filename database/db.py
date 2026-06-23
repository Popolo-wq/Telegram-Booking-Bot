"""Asynchronous SQLite data-access layer built on ``aiosqlite``.

All functions open a short-lived connection. For a bot of this size that is
simple and perfectly fast; a connection pool would be the next step at scale.
"""

from __future__ import annotations

from pathlib import Path

import aiosqlite

# booking.db sits next to the project root, schema.sql next to this module.
DB_PATH = Path(__file__).resolve().parent.parent / "booking.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


async def init_db() -> None:
    """Create tables and indexes if they do not exist yet."""
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.executescript(schema)
        await db.commit()


async def upsert_user(
    telegram_id: int, username: str | None, full_name: str | None
) -> int:
    """Insert the user or refresh their profile, returning the internal ``users.id``."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (telegram_id, username, full_name)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username  = excluded.username,
                full_name = excluded.full_name
            """,
            (telegram_id, username, full_name),
        )
        await db.commit()

        cursor = await db.execute(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        # row is guaranteed to exist after the upsert above.
        return int(row[0])


async def get_taken_slots(master: str, booking_date: str) -> set[str]:
    """Return the set of ``HH:MM`` slots already booked for a master on a date."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT substr(booking_datetime, 12, 5)
            FROM bookings
            WHERE master = ?
              AND date(booking_datetime) = ?
              AND status = 'active'
            """,
            (master, booking_date),
        )
        rows = await cursor.fetchall()
        return {row[0] for row in rows}


async def create_booking(
    user_id: int, service: str, master: str, booking_datetime: str
) -> int | None:
    """Create an active booking.

    Returns the new booking id, or ``None`` if the slot was taken in the
    meantime (enforced by the unique index — handles the race gracefully).
    """
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            cursor = await db.execute(
                """
                INSERT INTO bookings (user_id, service, master, booking_datetime, status)
                VALUES (?, ?, ?, ?, 'active')
                """,
                (user_id, service, master, booking_datetime),
            )
            await db.commit()
            return cursor.lastrowid
        except aiosqlite.IntegrityError:
            # Unique index tripped -> someone booked this exact slot first.
            return None


async def get_user_bookings(telegram_id: int, now: str) -> list[dict]:
    """Return a user's upcoming active bookings, soonest first."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT b.id, b.service, b.master, b.booking_datetime
            FROM bookings b
            JOIN users u ON u.id = b.user_id
            WHERE u.telegram_id = ?
              AND b.status = 'active'
              AND b.booking_datetime >= ?
            ORDER BY b.booking_datetime
            """,
            (telegram_id, now),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_today_bookings(today: str) -> list[dict]:
    """Return all active bookings for a given date (admin view)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT b.id, b.service, b.master, b.booking_datetime,
                   u.full_name, u.username
            FROM bookings b
            JOIN users u ON u.id = b.user_id
            WHERE date(b.booking_datetime) = ?
              AND b.status = 'active'
            ORDER BY b.booking_datetime
            """,
            (today,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
