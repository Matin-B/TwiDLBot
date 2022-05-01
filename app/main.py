from time import time
import logging
from aiogram import Bot, Dispatcher, executor, filters, types
from aiogram.types import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup, ContentType
from aiogram.utils.emoji import emojize
from pymongo import MongoClient
from twitter import download

import config

# Configure logging
logging.basicConfig(level=logging.INFO)


bot = Bot(
    token=config.BOT_TOKEN,
    parse_mode=ParseMode.HTML,
)

dp = Dispatcher(bot=bot)


@dp.message_handler(commands=["start"])
async def start_command_handler(message: types.Message):
    """
    This is the start command handler.
    """
    await message.reply(
        emojize(
            "Hi, Welcome to TwiDLBot :raised_hand:\n\n"
            "You can send an Tweet link to see and download."
            "Sample link:\nhttps://twitter.com/i/status/1481722124855169028"
            "\n\nOther bots:\n"
            "<a href='https://t.me/IgGramBot?start=ref_bot_TwiDLBot'>@IgGramBot</a>"
            ": IgGramBot is a bot that helps you download Instagram videos, photos,"
            " IGTV, Reels, Stories & Highlights Instagram from Telegram."
        ),
        disable_web_page_preview=True,
    )


@dp.message_handler(
    filters.Regexp(
        regexp=r"twitter.com\/.*\/status\/([0-9]*)",
    ),
)
async def tweet_link_handler(message: types.Message):
    """
    This handler will be called when user sends tweet link
    """
    replied_message = await message.reply(
        emojize(
            "Checking link ..."
        )
    )
    replied_message_id = replied_message.message_id

    error_gif = "https://media.giphy.com/media/sS8YbjrTzu4KI/giphy.gif"
    error_404_gif = "https://media.giphy.com/media/6uGhT1O4sxpi8/giphy.gif"

    tweet_link = message.text
    tweet_details = download(tweet_link)
    status = tweet_details["status"]
    status_code = tweet_details["status_code"]
    if status is True:
        type_name = tweet_details["type_name"]
        data = tweet_details["data"]
        if type_name == "text":
            pass
        elif type_name == "git":
            pass
        elif type_name == "video":
            pass
        elif type_name == "photo":
            pass
        elif type_name == "album":
            pass
    elif status is False and status_code == 404:
        status_message = tweet_details["message"]
        await replied_message.edit_text(
            emojize(
                f"<a href=\"{error_404_gif}\">&#160</a>" + status_message
            ),
        )
    else:
        await replied_message.edit_text(
            emojize(
                ":man_facepalming_light_skin_tone: There's something wrong ..."
                f"\n\nPlease try again later<a href=\"{error_gif}\">&#160</a>",
            ),
        )
            



@dp.message_handler(content_types=ContentType.ANY)
async def wrong_command(message: types.Message):
    await message.reply(
        "Please enter Tweet URL. Sample:\n"
        "https://twitter.com/i/status/1481722124855169028"
    )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
