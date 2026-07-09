from pymongo import MongoClient

from time import time
from config import MONGO_URI
from datetime import datetime, timezone

client = MongoClient(MONGO_URI)
db = client["telegram_bot"]

def add_user(user_id: int) -> None:
    """
    Adds a new user to the database if the user does not already exist.

    Args:
        user_id (int): The Telegram user's unique ID.
    """
    # Check if the user already exists
    if not db.users.find_one({"_id": user_id}):
        # Add user only if they do not exist
        db.users.insert_one({
            "_id": user_id,
            "timestamp": int(time())
        })


def get_user(user_id: int) -> dict:
    """
    Fetches user information from the database.
    """
    return db.users.find_one({"_id": user_id})

def save_file_record(user_id: int, file_id: str, file_unique_id: str, file_name: str, disk_path: str, download_link: str) -> None:
    """
    Saves the downloaded file metadata into the MongoDB 'files' collection.
    
    Args:
        user_id (int): The Telegram ID of the user who sent the file.
        file_id (str): Telegram's internal routing ID for the file (used for sending back to TG).
        file_unique_id (str): A persistent, unique ID for the file across all chats.
        file_name (str): The calculated or original name of the file.
        disk_path (str): The absolute path where the file is stored on the VPS.
        download_link (str): The public download link for the file.
    """
    document = {
        "user_id": user_id,
        "file_id": file_id,
        "file_unique_id": file_unique_id,
        "file_name": file_name,
        "disk_path": disk_path,
        "download_link": download_link,
        "created_at": datetime.now(timezone.utc)
    }
    
    # db is your global pymongo database instance defined at the top of the file
    db.files.insert_one(document)

