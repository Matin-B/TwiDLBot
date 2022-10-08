import logging
import os
from time import time

import requests
from aiogram import Bot, Dispatcher, executor, filters, types
from aiogram.types import (ChatActions, ContentType, InlineKeyboardButton,
                           InlineKeyboardMarkup, InputFile, ParseMode)
from aiogram.utils import exceptions
from emoji import emojize
from pymongo import MongoClient

import config
from twigram import download

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


def get_database():
    """
    Return database
    """
    # Create a connection
    client = MongoClient(config.MONGO_URI)

    # Get the database or create it if it doesn"t exist
    return client["TwiDLBot-DB"]


def save_tweet(tweet_type: str, data: dict) -> None:
    """
    Save tweet to database
    """
    database = get_database()
    collection = database["tweets"]

    collection.insert_one(data)


def download_video(download_url) -> str:
    """
    Download video from url
    
    :param download_url: The url of the video
    :return: The path to the video
    """
    VIDEOS_PATH = config.VOLUME_VIDEOS_PATH
    response = requests.get(download_url)
    file_name = download_url.split("?")[0].split("/")[-1]
    file_path = f"{VIDEOS_PATH}/{file_name}"
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size = 1024*1024): 
            if chunk:
                f.write(chunk)
    return file_path


def download_photo(download_url) -> str:
    """
    Download photo from url
    
    :param download_url: The url of the photo
    :return: The path to the photo
    """
    PHOTOS_PATH = config.VOLUME_PHOTOS_PATH
    response = requests.get(download_url)
    file_name = download_url.split("?")[0].split("/")[-1]
    file_path = f"{PHOTOS_PATH}/{file_name}"
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size = 1024*1024): 
            if chunk:
                f.write(chunk)
    return file_path


def remove_file(file_path):
    """
    Remove file from disk
    
    :param file_path: The path to the file
    """
    os.remove(file_path)


async def delete_message(chat_id: int, message_id: int):
    """
    It deletes the message that was replied to in the chat
    
    :param chat_id: The chat ID of the chat where the message will be deleted
    :param message_id: The message id to delete
    """
    await bot.delete_message(chat_id=chat_id, message_id=message_id)


def generate_caption(data: dict) -> str:
    """
    Return footer for caption
    """
    tweet_url = data["tweet_url"]
    tweet_text = data["tweet_text"]
    owner_name = data["owner_name"]
    owner_username = data["owner_username"]
    return (
        f"{tweet_text}\n\n"
        f":link: <a href='{tweet_url}'>{owner_name} (@{owner_username})</a>\n\n"
        f":robot: <a href='{BOT_URL}'>@{BOT_USERNAME}</a>\n"
        f":loudspeaker: <a href='{CHANNEL_URL}'>@{CHANNEL_USERNAME}</a>"
    )


async def send_text(chat_id: int, message_id: int, data: dict):
    """
    Send text message to user
    """
    caption = generate_caption(data)

    await ChatActions.typing()

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
    gif_url = data["gif_url"]

    caption = generate_caption(data)

    await ChatActions.upload_video()

    await bot.send_animation(
        chat_id=chat_id,
        animation=gif_url,
        caption=emojize(caption),
        reply_to_message_id=message_id,
    )


async def send_photo(chat_id: int, message_id: int, data: dict):
    """
    Send photo message to user
    """
    photo_url = data["photo_url"]
    
    caption = generate_caption(data)

    await ChatActions.upload_photo()

    try:
        await bot.send_photo(
            chat_id=chat_id,
            photo=photo_url,
            caption=emojize(caption),
            reply_to_message_id=message_id,
        )
    except exceptions.WrongFileIdentifier:
        photo_name = download_photo(photo_url)
        await bot.send_photo(
            chat_id=chat_id,
            photo=InputFile(photo_name),
            caption=emojize(caption),
            reply_to_message_id=message_id,
        )
        remove_file(photo_name)


async def send_album(chat_id: int, message_id: int, data: dict):
    """
    Send album (media group) message to user
    """
    photo_urls = data["photo_urls"]
    
    caption = generate_caption(data)

    try:
        media_group = types.MediaGroup()
        count = 0
        for photo in photo_urls:
            if count == 0:
                media_group.attach_photo(
                    photo=photo,
                    caption=emojize(caption),
                )
                count += 1
            else:
                media_group.attach_photo(photo=photo)

        await ChatActions.upload_photo()

        await bot.send_media_group(
            chat_id=chat_id,
            media=media_group,
            reply_to_message_id=message_id,
        )
    except exceptions.WrongFileIdentifier:
        media_group = types.MediaGroup()
        count = 0
        for photo in photo_urls:
            photo_name = download_photo(photo)
            if count == 0:
                media_group.attach_photo(
                    photo=InputFile(photo_name),
                    caption=emojize(caption),
                )
                count += 1
            else:
                media_group.attach_photo(photo=InputFile(photo_name))
            remove_file(photo_name)

        await ChatActions.upload_photo()

        await bot.send_media_group(
            chat_id=chat_id,
            media=media_group,
            reply_to_message_id=message_id,
        )


async def send_video(chat_id: int, message_id: int, data: dict):
    """
    Send video message to user
    """
    video_poster_url = data["video_poster_url"]
    video_urls = data["video_urls"]
    
    caption = generate_caption(data)

    keyboard = InlineKeyboardMarkup()
    for item in video_urls:
        quality = item["quality"]
        resolution = item["resolution"]
        download_url = item["url"]
        keyboard.row(
            InlineKeyboardButton(
                text=f"{resolution} ({quality})",
                url=download_url,
            )
        )
    high_quality_version = video_urls[0]
    high_quality_version_url = high_quality_version["url"]
    high_quality_version_size = high_quality_version["size"]
    high_quality_version_human_size = high_quality_version["human_size"]
    
    if high_quality_version_size < 20971520:
        await ChatActions.upload_video()
        try:
            await bot.send_video(
                chat_id=chat_id,
                video=high_quality_version_url,
                caption=emojize(caption),
                reply_to_message_id=message_id,
                reply_markup=keyboard,
            )
        except exceptions.WrongFileIdentifier:
            video_name = download_video(download_url)
            await bot.send_video(
                chat_id=chat_id,
                video=InputFile(video_name),
                caption=emojize(caption),
                reply_to_message_id=message_id,
                reply_markup=keyboard,
            )
            remove_file(video_name)
    else:
        await ChatActions.typing()
        text = (
            f"Sorry, this video is too big (It's {high_quality_version_human_size}).\n" 
            "Because of Telegram limitations(20 MB Max), we can't upload this file."
            "\nYou can download the file directly from the link below:\n\n" 
            f"<a href=\"{high_quality_version_url}\">:inbox_tray: Download</a>" 
            f" (Highest Quality)\n\n Tweet Text:\n{caption}"
        )
        await bot.send_message(
            chat_id=chat_id,
            text=emojize(text),
            reply_to_message_id=message_id,
            disable_web_page_preview=True,
            reply_markup=keyboard,
        )


@dp.message_handler(commands=["start"])
async def start_command_handler(message: types.Message):
    """
    This is the start command handler.
    """
    chat_id = message.chat.id
    user_first_name = message.from_user.first_name

    database = get_database()
    user_collection = database["users"]
    user_status = user_collection.find_one({"_id": chat_id})
    if user_status is None:
        user_collection.insert_one(
            {
                "_id": chat_id,
                "inserted_time": time(),
            }
        )
    
    await message.reply(
        emojize(
            f"Hi {user_first_name}, Welcome to TwiDLBot :raised_hand:\n"
            "Please send me a Tweet link to download.\n\n"
            "Sample link:\nhttps://twitter.com/i/status/1481722124855169028"
            "\n\nOther bots:\n"
            "<a href='https://t.me/IgGramBot?start=ref_bot_TwiDLBot'>@IgGramBot</a>: "
            "<b>IgGramBot allows you to download Instagram videos, photos, "
            "IGTV, Reels, Stories & Highlights from Telegram.</b>"
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

    tweet_link = message.text
    tweet_details = download(url=tweet_link, show_size=True)
    status = tweet_details["status"]
    if status is True:
        type_name = tweet_details["type_name"]
        data = tweet_details["data"]
        if type_name == "text":
            await delete_message(chat_id=chat_id, message_id=replied_message_id)
            await send_text(chat_id=chat_id, message_id=message_id, data=data)

        elif type_name == "gif":
            await delete_message(chat_id=chat_id, message_id=replied_message_id)
            await send_gif(chat_id=chat_id, message_id=message_id, data=data)

        elif type_name == "video":
            await delete_message(chat_id=chat_id, message_id=replied_message_id)
            await send_video(chat_id=chat_id, message_id=message_id, data=data)

        elif type_name == "photo":
            await delete_message(chat_id=chat_id, message_id=replied_message_id)
            await send_photo(chat_id=chat_id, message_id=message_id, data=data)

        elif type_name == "album":
            await delete_message(chat_id=chat_id, message_id=replied_message_id)
            await send_album(chat_id=chat_id, message_id=message_id, data=data)
    elif status is False and tweet_details["status_code"] == 404:
        status_message = tweet_details["message"]
        error_404_gif = "https://media.giphy.com/media/6uGhT1O4sxpi8/giphy.gif"
        await replied_message.edit_text(
            emojize(
                f"<a href=\"{error_404_gif}\">&#160</a>{status_message}"
            ),
        )
    else:
        error_gif = "https://media.giphy.com/media/sS8YbjrTzu4KI/giphy.gif"
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
            "The Tweet link should be entered in the following format:\n"
            "https://twitter.com/i/status/1481722124855169028"
        ),
        disable_web_page_preview=False,
    )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
