# 💈 Telegram Booking Bot

> A Telegram bot that automates barbershop appointment booking — customers book themselves in four taps, 24/7, with zero phone calls.



---

## ✨ Features

- **24/7 self-service booking** — customers book any time without a phone call or a receptionist.
- **Saves the admin ~2 hours/day** — no manual scheduling; the bot writes straight to the database.
- **No double-bookings** — taken time slots are hidden, and a database-level unique index blocks two people from grabbing the same slot at the same moment.
- **Guided 4-step flow** — service → master → date → time → confirm, powered by a Finite State Machine so the conversation never loses its place.
- **Instant confirmations** — every booking gets a unique ID (e.g. `BRB-00042`) the customer can quote later.
- **Customer self-service history** — `/mybookings` lists upcoming appointments on demand.
- **Owner dashboard** — `/admin` shows the day's schedule at a glance (admin-only).
- **Resilient** — handlers are wrapped in error handling and log failures instead of crashing.

---

## 🎬 Demo

📹 **30-second walkthrough:** _coming soon_ &nbsp;(video link and screenshots will be added here)

---

## 🛠 Tech Stack

| Layer        | Technology                          |
| ------------ | ----------------------------------- |
| Language     | Python 3.10+                        |
| Bot framework| [aiogram 3.x](https://docs.aiogram.dev) (async) |
| Conversation | aiogram FSM (Finite State Machine)  |
| Database     | SQLite via `aiosqlite` (async)      |
| Config       | `python-dotenv`                     |

---

## 🚀 Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/telegram-booking-bot.git
cd telegram-booking-bot

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env from the template
cp .env.example .env        # Windows: copy .env.example .env

# 5. Get a bot token from @BotFather on Telegram and paste it into .env
#    Also set ADMIN_USER_ID to your numeric Telegram id (ask @userinfobot).

# 6. Run the bot
python bot.py
```

The SQLite database (`booking.db`) is created automatically on first run.

---

## 📂 Project Structure

```
telegram-booking-bot/
├── README.md
├── requirements.txt
├── .env.example
├── bot.py                  # main entry point
├── handlers/
│   ├── __init__.py
│   ├── booking.py          # booking flow handlers (FSM)
│   ├── admin.py            # admin commands
│   └── common.py           # start, help, cancel, mybookings
├── keyboards/
│   ├── __init__.py
│   └── inline.py           # inline keyboard builders + callback factories
├── database/
│   ├── __init__.py
│   ├── db.py               # async SQLite setup & queries
│   └── schema.sql
├── config.py               # loads env vars + service catalog
└── states.py               # FSM states
```

---

## 🗄 Database Schema

**users**

| Column      | Type    | Notes                          |
| ----------- | ------- | ------------------------------ |
| id          | INTEGER | Primary key                    |
| telegram_id | INTEGER | Unique Telegram user id        |
| username    | TEXT    | `@handle` (nullable)           |
| full_name   | TEXT    | Display name                   |
| created_at  | TEXT    | Timestamp (defaults to now)    |

**bookings**

| Column           | Type    | Notes                                   |
| ---------------- | ------- | --------------------------------------- |
| id               | INTEGER | Primary key (used for `BRB-#####` code) |
| user_id          | INTEGER | FK → `users.id`                         |
| service          | TEXT    | e.g. "Haircut"                          |
| master           | TEXT    | e.g. "Aldiyar"                          |
| booking_datetime | TEXT    | `YYYY-MM-DD HH:MM`                       |
| status           | TEXT    | `active` / `cancelled`                  |
| created_at       | TEXT    | Timestamp (defaults to now)             |

> A partial unique index on `(master, booking_datetime) WHERE status = 'active'`
> guarantees a master can't be double-booked for the same slot.

---

## 🔮 Possible Extensions

- 📆 **Google Calendar sync** — push each booking to the master's calendar.
- 💳 **Payment integration** — take deposits via Telegram Payments / Stripe.
- 🔔 **SMS / push reminders** — reduce no-shows with a reminder the day before.
- 🌐 **Multi-language support** — serve customers in their preferred language.
- 📊 **Analytics dashboard** — busiest hours, revenue per master, repeat-customer rate.
