import asyncio
import os
import uvicorn
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from .scheduler import start_scheduler
from .api import app as fastapi_app

load_dotenv()

bot = Bot(token=os.getenv("TG_BOT_TOKEN"))
dp = Dispatcher()

# --- Команды ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("👋 Привет! Я бот BA Nightlife — сейчас всё проверим!")

@dp.message(Command("test"))
async def test_handler(message: types.Message):
    await message.answer("✅ Бот работает и слушает команды!")

# --- Главная функция ---
async def main():
    # Настройка uvicorn сервера
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    # Параллельно запускаем шедулер, телеграм-бота и API
    scheduler_task = asyncio.create_task(start_scheduler())
    bot_task = asyncio.create_task(dp.start_polling(bot))
    api_task = asyncio.create_task(server.serve())
    
    await asyncio.gather(scheduler_task, bot_task, api_task)

if __name__ == "__main__":
    asyncio.run(main())
