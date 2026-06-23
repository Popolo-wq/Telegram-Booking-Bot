-- Database schema for the Telegram Booking Bot.
-- Executed on startup via `executescript`; safe to run repeatedly.

CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL UNIQUE,
    username    TEXT,
    full_name   TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS bookings (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER NOT NULL REFERENCES users(id),
    service          TEXT NOT NULL,
    master           TEXT NOT NULL,
    booking_datetime TEXT NOT NULL,                  -- "YYYY-MM-DD HH:MM"
    status           TEXT NOT NULL DEFAULT 'active'
                          CHECK (status IN ('active', 'cancelled')),
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Prevents two active bookings for the same master at the same time
-- (guards against the race when two customers tap the same slot at once).
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_slot
    ON bookings (master, booking_datetime)
    WHERE status = 'active';

-- Speeds up the "today's bookings" admin query and per-user lookups.
CREATE INDEX IF NOT EXISTS idx_bookings_datetime ON bookings (booking_datetime);
CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings (user_id);
