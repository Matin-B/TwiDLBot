from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from emoji import emojize

router = Router()

@router.message(
    F.text.regexp(r"twitter.com\/.*\/status\/([0-9]*)"),
)
async def handle_twitter_links(message: Message) -> None:
    await message.reply(
        text=emojize(
            f"Hi"
        ),
    )
