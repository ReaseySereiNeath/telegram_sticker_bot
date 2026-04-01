import sys
import asyncio
from telethon import TelegramClient
from config.settings import API_ID, API_HASH, SESSION_FILE

async def main():
    if not API_ID or not API_HASH:
        print("ERROR: API_ID or API_HASH is not set in .env")
        sys.exit(1)
        
    print(f"Initializing Telethon session at {SESSION_FILE}.session...")
    client = TelegramClient(SESSION_FILE, int(API_ID), API_HASH)
    
    await client.connect()
    if not await client.is_user_authorized():
        print("\n=== Userbot Authorization ===")
        print("You are about to log in with your personal Telegram account to act as the userbot.")
        phone = input("Enter your phone number (with country code, e.g. +1234567890): ")
        await client.send_code_request(phone)
        
        try:
            code = input("Enter the login code you just received on Telegram: ")
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            password = input("2FA is enabled. Enter your password: ")
            await client.sign_in(password=password)
            
    print("\n✅ Success! Userbot is logged in and session is saved.")
    me = await client.get_me()
    print(f"Logged in as: {me.first_name} (@{me.username})")
    
    await client.disconnect()

if __name__ == "__main__":
    try:
        from telethon.errors import SessionPasswordNeededError
    except ImportError:
        pass
    asyncio.run(main())
