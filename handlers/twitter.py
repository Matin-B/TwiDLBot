from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from emoji import emojize
from utils.database import add_user

router = Router()

@router.message(Command("start"))
async def start_command(message: Message) -> None:
    add_user(message.from_user.id)

    await message.reply(
        text=emojize(
            f":cloud: <b>Welcome to TwiDLBot, {message.from_user.first_name}!</b>\n\n"
            "I can help you download videos or images from X (formerly Twitter)\n\n"
        ),
    )
