import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

async def list_dialogs():
    api_id = int(os.getenv("TG_API_ID"))
    api_hash = os.getenv("TG_API_HASH")
    session_name = os.getenv("TG_SESSION")
    
    client = TelegramClient(session_name, api_id, api_hash)
    await client.connect()
    
    async with client:
        print("--- DIALOGS ---")
        async for dialog in client.iter_dialogs():
            print(f"ID: {dialog.id} | Title: {dialog.title} | Type: {type(dialog.entity)}")
        print("----------------")

if __name__ == "__main__":
    asyncio.run(list_dialogs())
