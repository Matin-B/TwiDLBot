import re
from aiogram import Router, F
from aiogram.types import Message
from emoji import emojize

router = Router()

TWITTER_URL_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/[^/]+/status/([0-9]+)"
)

@router.message(F.text.regexp(TWITTER_URL_PATTERN))
async def handle_twitter_links(message: Message) -> None:
    await message.reply(
        text=emojize(
            f"Hi"
        ),
    )
