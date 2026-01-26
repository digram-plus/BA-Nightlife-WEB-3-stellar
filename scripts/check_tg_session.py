
import os
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

api_id = os.getenv("TG_API_ID")
api_hash = os.getenv("TG_API_HASH")
session_name = os.getenv("TG_SESSION", "ba_events_session")

async def main():
    async with TelegramClient(session_name, api_id, api_hash) as client:
        me = await client.get_me()
        print("\n=== Telegram Session Info ===")
        print(f"Name: {me.first_name} {me.last_name or ''}")
        print(f"Username: @{me.username or 'No username'}")
        print(f"ID: {me.id}")
        print(f"Phone: +{me.phone or 'Hidden'}")
        print("============================\n")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
