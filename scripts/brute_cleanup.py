import asyncio
import os
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()

async def brute_cleanup():
    bot = Bot(token=os.getenv("TG_BOT_TOKEN"))
    channel_id = os.getenv("TG_CHANNEL_ID")
    
    # We saw IDs up to 2057. Let's try to delete 1 to 2200.
    start_id = 1
    end_id = 2200
    
    print(f"Brute-force deleting messages {start_id} to {end_id} in {channel_id}...")
    
    deleted = 0
    for msg_id in range(end_id, start_id - 1, -1):
        try:
            await bot.delete_message(chat_id=channel_id, message_id=msg_id)
            deleted += 1
            if deleted % 50 == 0:
                print(f"Deleted {deleted} messages...")
        except Exception:
            # Most will fail because they don't exist or already deleted
            pass
        
        # Small sleep to be nice to the API
        if deleted % 30 == 0:
            await asyncio.sleep(0.05)

    print(f"Brute-force cleanup finished. Deleted {deleted} messages.")
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(brute_cleanup())
