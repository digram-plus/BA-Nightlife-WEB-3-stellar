
import os
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

async def main():
    api_id = int(os.getenv("TG_API_ID"))
    api_hash = os.getenv("TG_API_HASH")
    # We will use a new session name to avoid conflicts
    session_name = "ba_events_v2" 
    phone = "+541128927146"

    client = TelegramClient(session_name, api_id, api_hash)
    
    await client.connect()
    
    if not await client.is_user_authorized():
        print(f"Sending code to {phone}...")
        await client.send_code_request(phone)
        
        # This will wait for input from terminal
        code = input("ENTER TELEGRAM CODE: ")
        
        try:
            await client.sign_in(phone, code)
        except Exception as e:
            # If 2FA is enabled
            if "SessionPasswordNeededError" in str(type(e)) or "Password" in str(e) or "verification" in str(e).lower():
                password = input("ENTER 2FA PASSWORD: ")
                await client.sign_in(password=password)
            else:
                print(f"Error type: {type(e)}")
                raise e
                
    me = await client.get_me()
    print(f"\nSuccessfully logged in as: {me.first_name} (@{me.username})")
    print(f"New session file 'ba_events_v2.session' created.")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
