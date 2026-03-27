import os
import logging
from telethon import TelegramClient
from telethon.tl.functions.stickers import AddStickerToSetRequest
from telethon.tl.types import InputStickerSetShortName, InputStickerSetItem, DocumentAttributeSticker
from telethon.errors.rpcerrorlist import StickersetInvalidError, FloodWaitError
from config.settings import API_ID, API_HASH, SESSION_FILE, STICKER_PACK_NAME

logger = logging.getLogger(__name__)

class UserbotManager:
    def __init__(self):
        # We specify the session file path (Telethon appends .session automatically)
        self.client = TelegramClient(SESSION_FILE, int(API_ID), API_HASH) if API_ID and API_HASH else None

    async def start(self):
        if not self.client:
            logger.warning("Userbot client not initialized (check API_ID and API_HASH).")
            return
        
        logger.info("Starting Userbot client...")
        # Start without interactive phone prompt if it's already authorized.
        # If it's not authorized, this will raise an error unless we have a separate auth flow.
        try:
            await self.client.connect()
            if not await self.client.is_user_authorized():
                logger.error("Userbot is not authorized! Please run the interactive login script.")
            else:
                logger.info("Userbot started successfully.")
        except Exception as e:
            logger.error(f"Error starting userbot: {e}")

    async def stop(self):
        if self.client:
            logger.info("Stopping Userbot client...")
            await self.client.disconnect()

    async def add_sticker_to_pack(self, file_path: str, emoji: str = "😊") -> bool:
        """
        Uploads a file from disk and adds it to the sticker pack.
        """
        if not self.client or not await self.client.is_user_authorized():
            logger.error("Cannot add sticker: Userbot not authorized.")
            return False

        if not os.path.exists(file_path):
            logger.error(f"Cannot add sticker: File {file_path} not found.")
            return False

        try:
            # 1. Upload the file
            logger.info(f"Uploading file {file_path} for sticker pack...")
            uploaded_file = await self.client.upload_file(file_path)

            # 2. Add to pack
            logger.info(f"Adding uploaded file to pack {STICKER_PACK_NAME} with emoji {emoji}...")
            
            # The uploaded file doesn't have document attributes initially.
            # AddStickerToSet requires an InputDocument.
            # We must use messages.uploadMedia or similar to get an InputDocument if needed,
            # but AddStickerToSetRequest accepts InputDocument, which we can get by sending the media to ourselves,
            # OR we can just use the uploaded InputFile in some contexts?
            # Wait, AddStickerToSetRequest expects `InputDocument`. 
            # The easiest way to get an InputDocument from a file is to upload it and send it to a chat (e.g., "me"),
            # then grab the document attribute from the sent message.
            
            # Send to saved messages to generate a robust InputDocument
            msg = await self.client.send_file("me", uploaded_file, force_document=True)
            
            if not msg.document:
                logger.error("Sent message did not contain a document. Cannot add to sticker pack.")
                return False

            input_doc = msg.document

            sticker_item = InputStickerSetItem(
                document=input_doc,
                emoji=emoji,
                mask_coords=None
            )

            await self.client(AddStickerToSetRequest(
                stickerset=InputStickerSetShortName(short_name=STICKER_PACK_NAME),
                sticker=sticker_item
            ))

            logger.info("Sticker successfully added to pack.")
            
            # Cleanup the dummy message sent to 'me'
            await msg.delete()
            return True

        except StickersetInvalidError:
            logger.error(f"Sticker pack {STICKER_PACK_NAME} is invalid or not owned by this user.")
            return False
        except FloodWaitError as e:
            logger.error(f"Hit Telegram rate limit. Must wait {e.seconds} seconds.")
            return False
        except Exception as e:
            logger.error(f"Failed to add sticker: {e}")
            return False
