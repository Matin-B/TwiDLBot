import logging

from aiogram import Bot, Router
from aiogram.types import ErrorEvent
from emoji import emojize

# Ensure you have DEVELOPER_TELEGRAM_ID in your config.py
from config import DEVELOPER_TELEGRAM_ID

router = Router()

@router.errors()
async def error_router(event: ErrorEvent, bot: Bot) -> None:
    """Handles all exceptions raised during update processing."""
    
    update = event.update
    exception = event.exception
    
    logging.error(f"An error occurred while processing update: {update}")
    logging.error(f"Exception: {exception}")

    # Notify the developer via Telegram
    error_message = emojize(
        f":police_car_light: <b>An error occurred while processing an update.</b>\n\n"
        f"<b>Update ID:</b> {update.update_id if update else 'Unknown'}\n"
        f"<b>Exception:</b> <code>{exception}</code>"
    )
    
    try:
        await bot.send_message(
            chat_id=DEVELOPER_TELEGRAM_ID, 
            text=error_message
        )
    except Exception as e:
        logging.error(f"Failed to send error notification: {e}")