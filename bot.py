"""Main entry point for the Telegram Booking Bot.

Run with::

    python bot.py

Requires a valid BOT_TOKEN in the environment (see .env.example).
"""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from config import load_config
from database import db
from handlers import admin, booking, common

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot) -> None:
    """Register the command menu shown in the Telegram UI."""
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Book an appointment"),
            BotCommand(command="mybookings", description="My upcoming appointments"),
            BotCommand(command="cancel", description="Cancel current booking"),
            BotCommand(command="help", description="Show help"),
        ]
    )


async def main() -> None:
    """Configure and start the bot."""
    config = load_config()
    await db.init_db()

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Make the admin id available to handlers via workflow data injection.
    dp["admin_user_id"] = config.admin_user_id

    dp.include_router(common.router)
    dp.include_router(booking.router)
    dp.include_router(admin.router)

    await set_bot_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("Bot started. Polling for updates...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
