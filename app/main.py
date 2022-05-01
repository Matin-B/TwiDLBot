import logging
from time import time

from aiogram import Bot, Dispatcher, executor, filters, types
from aiogram.types import (ContentType, InlineKeyboardButton,
                           InlineKeyboardMarkup, ParseMode)
from aiogram.utils.emoji import emojize
from pymongo import MongoClient
from requests import delete

import config
from twitter import download

CHANNEL_USERNAME = config.CHANNEL_USERNAME
BOT_USERNAME = config.BOT_USERNAME
CHANNEL_URL = config.CHANNEL_URL
BOT_URL = config.BOT_URL

# Configure logging
logging.basicConfig(level=logging.INFO)


bot = Bot(
    token=config.BOT_TOKEN,
    parse_mode=ParseMode.HTML,
)

dp = Dispatcher(bot=bot)


async def delete_message(chat_id: int, message_id: int):
    """
    It deletes the message that was replied to in the chat
    
    :param chat_id: The chat ID of the chat where the message will be deleted
    :param message_id: The message id to delete
    """
    await bot.delete_message(chat_id=chat_id, message_id=message_id)


async def send_text(chat_id: int, message_id: int, data: dict):
    """
    Send text message to user
    """
    tweet_text = data["tweet_text"]
    tweet_url = data["tweet_url"]
    owner_name = data["owner_name"]
    owner_username = data["owner_username"]

    caption = (
        f"{tweet_text}\n\n"
        f":link: <a href='{tweet_url}'>{owner_name} (@{owner_username})</a>\n\n"
        f":robot: <a href='{BOT_URL}'>@{BOT_USERNAME}</a>\n"
        f":loudspeaker: <a href='{CHANNEL_URL}'>@{CHANNEL_USERNAME}</a>"
    )
    await bot.send_message(
        chat_id=chat_id,
        text=emojize(caption),
        reply_to_message_id=message_id,
        disable_web_page_preview=True,
    )


async def send_gif(chat_id: int, message_id: int, data: dict):
    """
    Send gif message to user
    """


async def send_photo(chat_id: int, message_id: int, data: dict):
    """
    Send photo message to user
    """


async def send_video(chat_id: int, message_id: int, data: dict):
    """
    Send video message to user
    """


async def send_album(chat_id: int, message_id: int, data: dict):
    """
    Send album (media group) message to user
    """


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
    chat_id = message.chat.id
    message_id = message.message_id

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
    if status is True:
        type_name = tweet_details["type_name"]
        data = tweet_details["data"]
        if type_name == "text":
            await delete_message(chat_id=chat_id, message_id=replied_message_id)
            await send_text(chat_id=chat_id, message_id=message_id, data=data)
        elif type_name == "git":
            pass
        elif type_name == "video":
            pass
        elif type_name == "photo":
            pass
        elif type_name == "album":
            pass
    elif status is False and tweet_details["status_code"] == 404:
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
async def invalid_format(message: types.Message):
    """
    This handler will be called when user sends invalid format
    """
    await message.reply(
        text=(
            "Please enter Tweet URL. Sample:\n"
            "https://twitter.com/i/status/1481722124855169028"
        ),
        disable_web_page_preview=True,
    )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
