import logging
import os
from time import time
from typing import Dict, Optional, List, Union
from pathlib import Path

import requests
from aiogram import Bot, Dispatcher, executor, filters, types
from aiogram.types import (
    ChatActions, ContentType, InlineKeyboardButton,
    InlineKeyboardMarkup, InputFile, ParseMode
)
from aiogram.utils import exceptions
from emoji import emojize
from pymongo import MongoClient

import config
from twigram import download

CHANNEL_USERNAME = config.CHANNEL_USERNAME
BOT_USERNAME = config.BOT_USERNAME
CHANNEL_URL = config.CHANNEL_URL
BOT_URL = config.BOT_URL

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot=bot)


def get_database():
    """Return database"""
    client = MongoClient(config.MONGO_URI)
    return client["TwiDLBot-DB"]


def save_tweet(tweet_type: str, data: dict) -> None:
    """Save tweet to database"""
    database = get_database()
    collection = database["tweets"]
    collection.insert_one(data)


def download_video(download_url: str) -> str:
    """Download video from url"""
    VIDEOS_PATH = config.VOLUME_VIDEOS_PATH
    Path(VIDEOS_PATH).mkdir(parents=True, exist_ok=True)
    
    response = requests.get(download_url, stream=True)
    response.raise_for_status()
    
    file_name = download_url.split("?")[0].split("/")[-1]
    file_path = f"{VIDEOS_PATH}/{file_name}"
    
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024*1024):
            if chunk:
                f.write(chunk)
    return file_path


def download_photo(download_url: str) -> str:
    """Download photo from url"""
    PHOTOS_PATH = config.VOLUME_PHOTOS_PATH
    Path(PHOTOS_PATH).mkdir(parents=True, exist_ok=True)
    
    response = requests.get(download_url, stream=True)
    response.raise_for_status()
    
    file_name = download_url.split("?")[0].split("/")[-1]
    file_path = f"{PHOTOS_PATH}/{file_name}"
    
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024*1024):
            if chunk:
                f.write(chunk)
    return file_path


def remove_file(file_path: str) -> None:
    """Remove file from disk"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logging.error(f"Failed to remove file {file_path}: {e}")


async def delete_message(chat_id: int, message_id: int):
    """Delete message from chat"""
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logging.error(f"Failed to delete message: {e}")


def generate_caption(data: dict) -> str:
    """Generate caption with tweet info"""
    return (
        f"{data['tweet_text']}\n\n"
        f":link: <a href='{data['tweet_url']}'>{data['owner_name']} (@{data['owner_username']})</a>\n\n"
        f":robot: <a href='{BOT_URL}'>@{BOT_USERNAME}</a>\n"
        f":loudspeaker: <a href='{CHANNEL_URL}'>@{CHANNEL_USERNAME}</a>"
    )


def build_video_keyboard(video_urls: List[dict]) -> InlineKeyboardMarkup:
    """Build keyboard with video quality options"""
    keyboard = InlineKeyboardMarkup()
    for item in video_urls:
        keyboard.row(
            InlineKeyboardButton(
                text=f"{item['resolution']} ({item['quality']})",
                url=item['url']
            )
        )
    return keyboard


async def send_text(chat_id: int, message_id: int, data: dict):
    """Send text message to user"""
    await ChatActions.typing()
    await bot.send_message(
        chat_id=chat_id,
        text=emojize(generate_caption(data)),
        reply_to_message_id=message_id,
        disable_web_page_preview=True,
    )


async def send_gif(chat_id: int, message_id: int, data: dict):
    """Send gif message to user"""
    await ChatActions.upload_video()
    await bot.send_animation(
        chat_id=chat_id,
        animation=data["gif_url"],
        caption=emojize(generate_caption(data)),
        reply_to_message_id=message_id,
    )


async def send_photo(chat_id: int, message_id: int, data: dict):
    """Send photo message to user"""
    await ChatActions.upload_photo()
    caption = emojize(generate_caption(data))
    
    try:
        await bot.send_photo(
            chat_id=chat_id,
            photo=data["photo_url"],
            caption=caption,
            reply_to_message_id=message_id,
        )
    except exceptions.WrongFileIdentifier:
        photo_path = download_photo(data["photo_url"])
        await bot.send_photo(
            chat_id=chat_id,
            photo=InputFile(photo_path),
            caption=caption,
            reply_to_message_id=message_id,
        )
        remove_file(photo_path)


async def send_album(chat_id: int, message_id: int, data: dict):
    """Send album (media group) message to user"""
    await ChatActions.upload_photo()
    caption = emojize(generate_caption(data))
    
    try:
        media_group = types.MediaGroup()
        for idx, photo_url in enumerate(data["photo_urls"]):
            if idx == 0:
                media_group.attach_photo(photo=photo_url, caption=caption)
            else:
                media_group.attach_photo(photo=photo_url)
        
        await bot.send_media_group(
            chat_id=chat_id,
            media=media_group,
            reply_to_message_id=message_id,
        )
    except exceptions.WrongFileIdentifier:
        media_group = types.MediaGroup()
        photo_paths = []
        
        try:
            for idx, photo_url in enumerate(data["photo_urls"]):
                photo_path = download_photo(photo_url)
                photo_paths.append(photo_path)
                
                if idx == 0:
                    media_group.attach_photo(photo=InputFile(photo_path), caption=caption)
                else:
                    media_group.attach_photo(photo=InputFile(photo_path))
            
            await bot.send_media_group(
                chat_id=chat_id,
                media=media_group,
                reply_to_message_id=message_id,
            )
        finally:
            for path in photo_paths:
                remove_file(path)


async def send_video(chat_id: int, message_id: int, data: dict):
    """Send video message to user"""
    await ChatActions.upload_video()
    caption = emojize(generate_caption(data))
    video_urls = data["video_urls"]
    
    keyboard = build_video_keyboard(video_urls)
    best_video = video_urls[0]
    
    if best_video["size"] < 20971520:  # 20 MB
        try:
            await bot.send_video(
                chat_id=chat_id,
                video=best_video["url"],
                caption=caption,
                reply_to_message_id=message_id,
                reply_markup=keyboard,
            )
        except exceptions.WrongFileIdentifier:
            video_path = download_video(best_video["url"])
            await bot.send_video(
                chat_id=chat_id,
                video=InputFile(video_path),
                caption=caption,
                reply_to_message_id=message_id,
                reply_markup=keyboard,
            )
            remove_file(video_path)
    else:
        await ChatActions.typing()
        text = (
            f"⚠️ <b>Video too large</b>\n\n"
            f"Size: {best_video['human_size']} (limit: 20 MB)\n\n"
            f"📥 <a href='{best_video['url']}'>Download Original</a> (Highest Quality)\n\n"
            f"<i>{caption}</i>"
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
    """Handle /start command"""
    chat_id = message.chat.id
    
    database = get_database()
    user_collection = database["users"]
    if not user_collection.find_one({"_id": chat_id}):
        user_collection.insert_one({"_id": chat_id, "inserted_time": time()})
    
    welcome_text = (
        f"Hi {message.from_user.first_name}, Welcome to TwiDLBot :raised_hand:\n\n"
        f"📎 Send me a Tweet link to download\n\n"
        f"📝 Example:\n"
        f"<code>https://twitter.com/i/status/1481722124855169028</code>\n\n"
        f"🤖 Other bots:\n"
        f"<a href='https://t.me/IgGramBot?start=ref_bot_TwiDLBot'>@IgGramBot</a>: "
        f"<b>Download Instagram videos, photos, IGTV, Reels & Stories</b>"
    )
    
    await message.reply(
        emojize(welcome_text),
        disable_web_page_preview=True,
    )


@dp.message_handler(filters.Regexp(regexp=r"twitter\.com\/.*\/status\/([0-9]*)"))
async def tweet_link_handler(message: types.Message):
    """Handle tweet links"""
    chat_id = message.chat.id
    message_id = message.message_id
    
    status_msg = await message.reply(emojize("🔍 Checking link..."))
    
    tweet_details = download(url=message.text, show_size=True)
    
    if tweet_details.get("status"):
        await delete_message(chat_id, status_msg.message_id)
        
        handlers = {
            "text": send_text,
            "gif": send_gif,
            "video": send_video,
            "photo": send_photo,
            "album": send_album,
        }
        
        handler = handlers.get(tweet_details["type_name"])
        if handler:
            await handler(chat_id, message_id, tweet_details["data"])
            
    elif tweet_details.get("status_code") == 404:
        await status_msg.edit_text(
            emojize(f"<a href='https://media.giphy.com/media/6uGhT1O4sxpi8/giphy.gif'>&#160</a>"
                   f"{tweet_details.get('message', 'Tweet not found')}")
        )
    else:
        await status_msg.edit_text(
            emojize(":man_facepalming_light_skin_tone: Something went wrong...\n\n"
                   f"<a href='https://media.giphy.com/media/sS8YbjrTzu4KI/giphy.gif'>&#160</a>"
                   "Please try again later")
        )


@dp.message_handler(content_types=ContentType.ANY)
async def invalid_format(message: types.Message):
    """Handle invalid message format"""
    await message.reply(
        "❌ <b>Invalid format</b>\n\n"
        "Please send a valid Twitter link:\n"
        "<code>https://twitter.com/i/status/1481722124855169028</code>"
    )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
