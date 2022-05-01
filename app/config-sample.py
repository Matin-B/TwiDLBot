# Main Bot
BOT_TOKEN = "YOUR_BOT_TOKEN"


# Production DB
MONGO_HOST = ""
MONGO_PORT = ""
MONGO_USERNAME = ""
MONGO_PASSWORD = ""
MONGO_URI = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@"\
            f"{MONGO_HOST}:{MONGO_PORT}/my-app?authSource=admin"


BOT_USERNAME = ""
BOT_URL = f"https://t.me/{BOT_USERNAME}"
CHANNEL_URL = "https://t.me/"

PRIVATE_CHANNEL_DB = int("") # Sample: -100123456789
PUBLIC_CHANNEL_DB = int("")


ADMIN_LIST = [
    711692445, # Matin
    258872582, # Amir
]
