import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import FilesPathWrapper, TelegramAPIServer
from aiogram.enums import ParseMode

from config import BOT_API_TOKEN, LOCAL_API_URL
from handlers import error, start, twitter

class DockerFilesPathWrapper(FilesPathWrapper):
    """
    Translates filesystem paths between the local API server (Docker) 
    and the Python application host (VPS).
    """
    def __init__(self, server_path: str, client_path: str) -> None:
        self.server_path = server_path
        self.client_path = client_path

    def to_local(self, path: Path | str) -> Path | str:
        """Translates the path from the Docker container to the VPS host."""
        return Path(str(path).replace(self.server_path, self.client_path))

    def to_server(self, path: Path | str) -> Path | str:
        """Translates the path from the VPS host back to the Docker container."""
        return Path(str(path).replace(self.client_path, self.server_path))

# Configure logging
logging.basicConfig(level=logging.INFO)

# Instantiate the wrapper with your specific VPS and Docker directories
path_wrapper = DockerFilesPathWrapper(
    server_path="/var/lib/telegram-bot-api",
    client_path="/opt/telegram-bot-api"
)

# Initialize the local server and inject the custom path wrapper
local_server = TelegramAPIServer.from_base(
    LOCAL_API_URL, 
    is_local=True,
    wrap_local_file=path_wrapper
)

# Attach the custom server to a new HTTP session
session = AiohttpSession(
    api=local_server,
)

# Initialize bot and dispatcher
bot = Bot(
    token=BOT_API_TOKEN,
    session=session,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Include routers from handlers
dp.include_router(start.router)
dp.include_router(error.router)
dp.include_router(twitter.router)

async def main() -> None:
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())