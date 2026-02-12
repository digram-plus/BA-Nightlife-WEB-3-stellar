import os
import asyncio
from telethon import TelegramClient
from app.db import SessionLocal
from app.models import Event

async def deep_cleanup():
    api_id = int(os.getenv("TG_API_ID"))
    api_hash = os.getenv("TG_API_HASH")
    session_name = os.getenv("TG_SESSION")
    channel_id = os.getenv("TG_CHANNEL_ID")
    
    if channel_id.startswith("-100"):
        channel_id = int(channel_id)

    client = TelegramClient(session_name, api_id, api_hash)
    
    print("Connecting to Telegram...")
    await client.connect()
    
    if not await client.is_user_authorized():
        print("User not authorized. Please run login_new_session.py first.")
        return

    async with client:
        print(f"Resolving entity for channel {channel_id}...")
        entity = None
        try:
            entity = await client.get_entity(channel_id)
        except Exception as e:
            print(f"Direct ID resolution failed: {e}")
            
            # Try PeerChannel with stripped ID
            from telethon.tl.types import PeerChannel
            cid_str = str(channel_id)
            if cid_str.startswith("-100"):
                stripped_id = int(cid_str[4:])
                try:
                    print(f"Trying PeerChannel stripping -100: {stripped_id}")
                    entity = await client.get_entity(PeerChannel(stripped_id))
                except Exception as e2:
                    print(f"PeerChannel resolution failed: {e2}")

            if not entity:
                print("Iterating dialogs to find channel...")
                async for dialog in client.iter_dialogs():
                    # Compare IDs or names as fallback
                    if dialog.id == channel_id or str(dialog.id).endswith(cid_str[-10:]):
                        print(f"Found matching dialog: {dialog.name} ({dialog.id})")
                        entity = dialog.entity
                        break
        
        if not entity:
            raise ValueError(f"Could not find channel with ID {channel_id}")

        print(f"Starting deep cleanup for {getattr(entity, 'title', 'Unknown')}...")
        
        # Delete messages - use a list to avoid iterator issues during deletion
        message_ids = []
        async for message in client.iter_messages(entity, limit=2000):
            message_ids.append(message.id)
        
        if not message_ids:
            print("No messages found to delete.")
        else:
            print(f"Deleting {len(message_ids)} messages in batches...")
            # Delete in chunks of 100
            for i in range(0, len(message_ids), 100):
                batch = message_ids[i:i+100]
                await client.delete_messages(entity, batch)
                print(f"Deleted batch {i//100 + 1}...")
                await asyncio.sleep(1.0)
        
        print(f"Total messages deleted from channel: {deleted_count}")

    # Clear Database
    print("Clearing database...")
    db = SessionLocal()
    try:
        db.query(Event).delete()
        db.commit()
        print("Database events cleared.")
    except Exception as e:
        print(f"Error clearing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(deep_cleanup())
