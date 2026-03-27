import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Telegram API Credentials
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# Parse Admin IDs into a set of integers
admin_ids_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = set()
if admin_ids_str:
    try:
        ADMIN_IDS = {int(x.strip()) for x in admin_ids_str.split(",") if x.strip()}
    except ValueError:
        pass

# Sticker Pack Constants
STICKER_PACK_NAME = os.getenv("STICKER_PACK_NAME", "MyAwesomePack")

# Storage Paths
STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")
SESSION_FILE = os.path.join(STORAGE_DIR, "user")
QUEUE_FILE = os.path.join(STORAGE_DIR, "submissions.json")
