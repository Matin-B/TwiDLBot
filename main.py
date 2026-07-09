import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_API_TOKEN
from handlers import error, start, twitter

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(
    token=BOT_API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Include routers from handlers
dp.include_router(start.router)
dp.include_router(error.router)
dp.include_router(twitter.router)

async def main() -> None:
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())