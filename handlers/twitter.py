import os
import re
import requests

from aiogram import Bot, Router, F
from aiogram.types import (
    Message,
    FSInputFile,
    InputMediaPhoto,
    InputMediaVideo,
    LinkPreviewOptions
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from emoji import emojize

from twigram import download
from config import BOT_URL, BOT_USERNAME, CHANNEL_URL, CHANNEL_USERNAME, VOLUME_VIDEOS_PATH, VOLUME_PHOTOS_PATH

router = Router()

TWITTER_URL_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/[^/]+/status/([0-9]+)"
)

def download_photo(download_url: str) -> str:
    """
    Download photo from url
    
    :param download_url: The url of the photo
    :return: The path to the photo
    """
    response = requests.get(download_url)
    file_name = download_url.split("?")[0].split("/")[-1]
    file_path = f"{VOLUME_PHOTOS_PATH}/{file_name}"
    
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024): 
            if chunk:
                f.write(chunk)
    return file_path


def download_video(download_url: str) -> str:
    """
    Download video from url
    
    :param download_url: The url of the video
    :return: The path to the video
    """
    response = requests.get(download_url)
    file_name = download_url.split("?")[0].split("/")[-1]
    file_path = f"{VOLUME_VIDEOS_PATH}/{file_name}"
    
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024): 
            if chunk:
                f.write(chunk)
    return file_path


def remove_file(file_path: str) -> None:
    """
    Remove file from disk
    
    :param file_path: The path to the file
    """
    if os.path.exists(file_path):
        os.remove(file_path)


def generate_caption(data: dict) -> str:
    """
    Return footer for caption
    """
    tweet_url = data["tweet_url"]
    tweet_text = data["tweet_text"]
    owner_name = data["owner_name"]
    owner_username = data["owner_username"]
    
    return (
        f"{tweet_text}\n\n\n"
        f":link: <a href=\"{tweet_url}\">{owner_name} (@{owner_username})</a>\n\n"
        f":robot: <a href=\"{BOT_URL}\">@{BOT_USERNAME}</a>\n"
        f":loudspeaker: <a href=\"{CHANNEL_URL}\">@{CHANNEL_USERNAME}</a>"
    )


async def send_text(bot: Bot, chat_id: int, message_id: int, data: dict) -> None:
    """
    Send text message to user
    """
    caption = generate_caption(data)

    await bot.send_chat_action(chat_id=chat_id, action="typing")

    await bot.send_message(
        chat_id=chat_id,
        text=emojize(caption),
        reply_to_message_id=message_id,
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


async def send_gif(bot: Bot, chat_id: int, message_id: int, data: dict) -> None:
    """
    Send gif message to user
    """
    gif_url = data["gif_url"]
    caption = generate_caption(data)

    await bot.send_chat_action(chat_id=chat_id, action="upload_video")

    await bot.send_animation(
        chat_id=chat_id,
        animation=gif_url,
        caption=emojize(caption),
        reply_to_message_id=message_id,
    )


async def send_photo(bot: Bot, chat_id: int, message_id: int, data: dict) -> None:
    """
    Send photo message to user
    """
    photo_url = data["photo_url"]
    caption = generate_caption(data)

    await bot.send_chat_action(chat_id=chat_id, action="upload_photo")

    try:
        await bot.send_photo(
            chat_id=chat_id,
            photo=photo_url,
            caption=emojize(caption),
            reply_to_message_id=message_id,
        )
    except TelegramBadRequest:
        # If Telegram rejects the remote URL, download it and send as FSInputFile
        photo_name = download_photo(photo_url)
        await bot.send_photo(
            chat_id=chat_id,
            photo=FSInputFile(photo_name),
            caption=emojize(caption),
            reply_to_message_id=message_id,
        )
        remove_file(photo_name)


async def send_album(bot: Bot, chat_id: int, message_id: int, data: dict) -> None:
    """
    Send album (media group) message to user
    """
    urls = data["urls"]
    caption = emojize(generate_caption(data))


    await bot.send_chat_action(chat_id=chat_id, action="typing")

    media_group = []
    for item in urls:
        item_type = item["type"]
        item_url = item["url"]
        if item_type == "photo":
            media_group.append(InputMediaPhoto(media=item_url, caption=caption))
        elif item_type == "video":
            media_group.append(InputMediaVideo(media=item_url, caption=caption))

    try:
        sended_album_message = await bot.send_media_group(
            chat_id=chat_id,
            media=media_group,
            reply_to_message_id=message_id,
        )
        sended_album_message_id = sended_album_message[0].message_id
        await bot.send_message(
            chat_id=chat_id,
            text=caption,
            reply_to_message_id=sended_album_message_id,
        )
    except TelegramBadRequest:
        # Fallback: Download all photos and build a new media group with FSInputFile
        fallback_media_group = []
        downloaded_files = []

        for item in urls:
            item_type = item["type"]
            item_url = item["url"]
            if item_type == "photo":
                photo_name = download_photo(item_url)
                downloaded_files.append(photo_name)
                fallback_media_group.append(
                    InputMediaPhoto(media=FSInputFile(photo_name), caption=caption)
                )
            elif item_type == "video":
                video_name = download_video(item_url)
                downloaded_files.append(video_name)
                fallback_media_group.append(
                    InputMediaVideo(media=FSInputFile(video_name), caption=caption)
                )

        sended_album_message = await bot.send_media_group(
            chat_id=chat_id,
            media=fallback_media_group,
            reply_to_message_id=message_id,
        )
        sended_album_message_id = sended_album_message[0].message_id
        await bot.send_message(
            chat_id=chat_id,
            text=caption,
            reply_to_message_id=sended_album_message_id,
        )

        
        # Cleanup downloaded files
        for file_path in downloaded_files:
            remove_file(file_path)


async def send_video(bot: Bot, chat_id: int, message_id: int, data: dict) -> None:
    """
    Send video message to user
    """
    video_urls = data["video_urls"]
    caption = generate_caption(data)

    keyboard_builder = InlineKeyboardBuilder()
    for item in video_urls:
        keyboard_builder.button(
            text=f"{item['resolution']} ({item['quality']})",
            url=item["url"],
        )
    keyboard_builder.adjust(1)
    
    high_quality_version = video_urls[0]
    high_quality_version_url = high_quality_version["url"]
    high_quality_version_size = high_quality_version["size"]
    high_quality_version_human_size = high_quality_version["human_size"]
    
    # 2000MB limit in bytes
    if high_quality_version_size < 2097152000:
        await bot.send_chat_action(chat_id=chat_id, action="upload_video")
        try:
            await bot.send_video(
                chat_id=chat_id,
                video=high_quality_version_url,
                caption=emojize(caption),
                reply_to_message_id=message_id,
                reply_markup=keyboard_builder.as_markup(),
            )
        except TelegramBadRequest:
            video_name = download_video(high_quality_version_url)
            await bot.send_video(
                chat_id=chat_id,
                video=FSInputFile(video_name),
                caption=emojize(caption),
                reply_to_message_id=message_id,
                reply_markup=keyboard_builder.as_markup(),
            )
            remove_file(video_name)
    else:
        await bot.send_chat_action(chat_id=chat_id, action="typing")
        text = (
            f"Sorry, this video is too big (It's {high_quality_version_human_size}).\n" 
            "Because of Telegram limitations (20 MB Max), we can't upload this file."
            "\nYou can download the file directly from the link below:\n\n" 
            f"<a href=\"{high_quality_version_url}\">:inbox_tray: Download</a>" 
            f" (Highest Quality)\n\n Tweet Text:\n{caption}"
        )
        await bot.send_message(
            chat_id=chat_id,
            text=emojize(text),
            reply_to_message_id=message_id,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
            reply_markup=keyboard_builder.as_markup(),
        )


@router.message(F.text.regexp(TWITTER_URL_PATTERN))
async def handle_twitter_links(message: Message, bot: Bot) -> None:
    """
    Main handler for Twitter/X links.
    Notice we added `bot: Bot` to the signature so Aiogram injects it contextually.
    """
    chat_id = message.chat.id
    message_id = message.message_id

    replied_message = await message.reply(
        emojize(":hourglass_not_done: Processing link ..."),
    )
    
    tweet_url = message.text
    twigram_response = download(tweet_url, show_size=True)
    
    if not twigram_response["status"]:
        error_gif = "https://media.giphy.com/media/sS8YbjrTzu4KI/giphy.gif"
        await replied_message.edit_text(
            emojize(
                ":man_facepalming_light_skin_tone: There's something wrong ..."
                f"<a href=\"{error_gif}\">&#160</a>"
            ),
        )
    else:
        type_name = twigram_response["type_name"]
        data = twigram_response["data"]
        
        await bot.delete_message(chat_id=chat_id, message_id=replied_message.message_id)

        if type_name == "text":
            await send_text(bot, chat_id, message_id, data)
        elif type_name == "gif":
            await send_gif(bot, chat_id, message_id, data)
        elif type_name == "photo":
            await send_photo(bot, chat_id, message_id, data)
        elif type_name == "album":
            await send_album(bot, chat_id, message_id, data)
        elif type_name == "video":
            await send_video(bot, chat_id, message_id, data)