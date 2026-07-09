from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from emoji import emojize
from utils.database import add_user

router = Router()

@router.message(Command("start"))
async def start_command(message: Message) -> None:
    add_user(message.from_user.id)

    await message.reply(
        text=emojize(
            f":cloud: <b>Welcome to GetPublicURL, {message.from_user.first_name}!</b>\n\n"
            f"I act as a high-speed bridge between Telegram and the public internet.\n\n"
            f":inbox_tray: <b>How to use:</b>\n"
            f"Simply upload or forward any file (video, audio, document) to this chat. "
            f"I will process the metadata and return a direct, shareable web link instantly.\n\n"
            f"<i>Waiting for your first file...</i>"
        ),
    )
