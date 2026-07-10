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


def save_tweet(data: dict) -> None:
    """
    Save tweet to database.
    """
    db.tweets.insert_one(data)