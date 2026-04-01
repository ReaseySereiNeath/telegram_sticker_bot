import logging
from telegram import Update
from telegram.ext import ContextTypes
import emoji as emj # Requires `emoji` package (I will need to add it to requirements.txt)
from .admin import queue_manager
from config.settings import ADMIN_IDS

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    user = update.effective_user
    welcome_text = (
        f"Hi {user.first_name}! 👋\n\n"
        "Send me a Sticker, a PNG, a WebP, or a Photo to submit it to our sticker pack.\n\n"
        "If you want a specific emoji for your sticker, just write the emoji in the photo/file caption! "
        "Otherwise, I'll default to 😊.\n\n"
        "Once an admin approves it, I will let you know!"
    )
    await update.message.reply_text(welcome_text)

def extract_emoji(text: str) -> str:
    """Extracts the first emoji found in a string, or returns None."""
    if not text:
        return None
    for char in text:
        if emj.is_emoji(char):
            return char
    return None

async def submission_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming media (stickers, photos, documents)."""
    message = update.message
    user = update.effective_user
    
    file_id = None
    file_unique_id = None
    original_file_name = None
    caption = message.caption or message.text or ""
    
    # Check if blocked
    if queue_manager.is_blocked(user.id):
        return

    # Rate limiting (max 3 per hour)
    if queue_manager.get_user_submission_count_last_hour(user.id) >= 3:
        await message.reply_text("⚠️ You have reached the maximum of 3 submissions per hour. Please try again later.")
        return

    # 1. Detect media type and extract IDs
    file_size = 0
    if message.sticker:
        file_id = message.sticker.file_id
        file_unique_id = message.sticker.file_unique_id
        file_size = message.sticker.file_size or 0
        if not extract_emoji(caption) and message.sticker.emoji:
            caption = message.sticker.emoji
    elif message.photo:
        best_photo = message.photo[-1]
        file_id = best_photo.file_id
        file_unique_id = best_photo.file_unique_id
        file_size = best_photo.file_size or 0
    elif message.document:
        doc = message.document
        if doc.mime_type in ["image/png", "image/webp", "image/jpeg"]:
            file_id = doc.file_id
            file_unique_id = doc.file_unique_id
            file_size = doc.file_size or 0
            original_file_name = doc.file_name
        else:
            await message.reply_text("❌ Please send a valid image format (PNG, WebP, JPEG).")
            return
    else:
        return

    # Max file size check (e.g. 5MB)
    if file_size > 5 * 1024 * 1024:
        await message.reply_text("❌ File is too large. Maximum allowed size is 5MB.")
        return


    # 2. Extract emoji
    selected_emoji = extract_emoji(caption)
    if not selected_emoji:
        selected_emoji = "😊"

    # 3. Add to queue
    submission = queue_manager.add_submission(
        from_user_id=user.id,
        from_user_name=user.full_name,
        file_id=file_id,
        file_unique_id=file_unique_id,
        emoji=selected_emoji,
        original_file_name=original_file_name
    )

    if not submission:
        await message.reply_text(
            "⚠️ This exact file has already been submitted to the queue!"
        )
        return

    # 4. Confirm submission
    await message.reply_text(
        f"✅ **Submission Received!**\n\n"
        f"**ID:** `{submission['id']}`\n"
        f"**Emoji:** {selected_emoji}\n\n"
        f"Your submission is now pending admin approval.",
        parse_mode="Markdown"
    )
    logger.info(f"New submission {submission['id']} from {user.id}")

    # Notify admins
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"📩 *New submission!*\n\n"
                     f"*ID:* `{submission['id']}`\n"
                     f"*From:* {user.full_name} (`{user.id}`)\n"
                     f"*Emoji:* {selected_emoji}\n\n"
                     f"Use /approve {submission['id']} or /pending to review.",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")
