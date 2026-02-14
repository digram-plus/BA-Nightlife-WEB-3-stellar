import asyncio
import os
from decimal import Decimal, InvalidOperation

import httpx
import uvicorn
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from .scheduler import start_scheduler
from .api import app as fastapi_app
from .services.payments_client import create_payment_intent, get_payment_status

load_dotenv()

bot = Bot(token=os.getenv("TG_BOT_TOKEN"))
dp = Dispatcher()
INTERNAL_API_BASE_URL = os.getenv("INTERNAL_API_BASE_URL", "http://127.0.0.1:8000")
PAYMENT_DEFAULT_CURRENCY = os.getenv("PAYMENT_DEFAULT_CURRENCY", "ARS").upper()
SUPPORTED_PAYMENT_PROVIDERS = {"moneygram", "airtm"}


def _parse_decimal_amount(raw: str) -> Decimal:
    normalized = raw.strip().replace(",", ".")
    amount = Decimal(normalized)
    if amount <= 0:
        raise InvalidOperation("amount must be positive")
    return amount.quantize(Decimal("0.01"))


def _parse_payment_args(text: str) -> tuple[int, Decimal, str | None]:
    parts = text.split()
    if len(parts) < 3:
        raise ValueError("usage")
    event_id = int(parts[1])
    amount = _parse_decimal_amount(parts[2])
    provider = parts[3].strip().lower() if len(parts) > 3 else None
    if provider and provider not in SUPPORTED_PAYMENT_PROVIDERS:
        raise ValueError("provider")
    return event_id, amount, provider


def _build_checkout_keyboard(checkout_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Open Checkout", url=checkout_url)],
        ]
    )


def _format_status_message(status_payload: dict) -> str:
    provider_status = status_payload.get("provider_status") or "-"
    failure_reason = status_payload.get("failure_reason") or "-"
    return (
        "Payment status\n"
        f"ID: {status_payload.get('payment_id')}\n"
        f"Provider: {status_payload.get('provider')}\n"
        f"Status: {status_payload.get('status')}\n"
        f"Provider status: {provider_status}\n"
        f"Failure reason: {failure_reason}\n"
        f"Amount: {status_payload.get('fiat_amount')} {status_payload.get('fiat_currency')}"
    )

# --- Команды ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Привет! Я бот BA Nightlife.\n"
        "Payment commands:\n"
        "/pay <event_id> <amount_ars> [moneygram|airtm]\n"
        "/donate <event_id> <amount_ars> [moneygram|airtm]\n"
        "/pay_status <payment_id>"
    )

@dp.message(Command("test"))
async def test_handler(message: types.Message):
    await message.answer("✅ Бот работает и слушает команды!")


async def _start_payment(message: types.Message, *, kind: str) -> None:
    if not message.text:
        return
    try:
        event_id, amount, provider = _parse_payment_args(message.text)
    except ValueError as e:
        if str(e) == "provider":
            await message.answer("Unknown provider. Use moneygram or airtm.")
            return
        await message.answer(
            "Usage:\n"
            f"/{'pay' if kind == 'ticket' else 'donate'} <event_id> <amount_ars> [moneygram|airtm]\n"
            "Example: /pay 123 15000 moneygram"
        )
        return
    except (InvalidOperation, TypeError):
        await message.answer("Invalid amount. Use positive number, e.g. 15000 or 15000.50")
        return
    except Exception:
        await message.answer("Invalid command format.")
        return

    try:
        payload = await create_payment_intent(
            base_url=INTERNAL_API_BASE_URL,
            event_id=event_id,
            fiat_amount=amount,
            fiat_currency=PAYMENT_DEFAULT_CURRENCY,
            kind=kind,
            preferred_provider=provider,
            telegram_user_id=message.from_user.id if message.from_user else None,
            metadata={
                "source": "telegram_bot",
                "chat_id": str(message.chat.id),
                "command": "pay" if kind == "ticket" else "donate",
            },
        )
    except httpx.HTTPStatusError as e:
        detail = "Unknown error"
        try:
            detail = e.response.json().get("detail", detail)
        except Exception:
            pass
        await message.answer(f"Failed to create payment: {detail}")
        return
    except Exception as e:
        await message.answer(f"Failed to create payment: {e}")
        return

    checkout_url = payload["checkout_url"]
    payment_id = payload["payment_id"]
    provider_name = payload["provider"]
    await message.answer(
        "Payment created.\n"
        f"Payment ID: {payment_id}\n"
        f"Provider: {provider_name}\n"
        f"Amount: {payload['fiat_amount']} {payload['fiat_currency']}\n"
        f"Type: {payload['kind']}\n\n"
        f"After checkout, check status with /pay_status {payment_id}",
        reply_markup=_build_checkout_keyboard(checkout_url),
        disable_web_page_preview=True,
    )


@dp.message(Command("pay"))
async def pay_handler(message: types.Message):
    await _start_payment(message, kind="ticket")


@dp.message(Command("donate"))
async def donate_handler(message: types.Message):
    await _start_payment(message, kind="donation")


@dp.message(Command("pay_status"))
async def pay_status_handler(message: types.Message):
    if not message.text:
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Usage: /pay_status <payment_id>")
        return
    payment_id = parts[1].strip()
    if not payment_id:
        await message.answer("Usage: /pay_status <payment_id>")
        return

    try:
        status_payload = await get_payment_status(base_url=INTERNAL_API_BASE_URL, payment_id=payment_id)
    except httpx.HTTPStatusError as e:
        detail = "Unknown error"
        try:
            detail = e.response.json().get("detail", detail)
        except Exception:
            pass
        await message.answer(f"Failed to fetch status: {detail}")
        return
    except Exception as e:
        await message.answer(f"Failed to fetch status: {e}")
        return

    await message.answer(_format_status_message(status_payload), disable_web_page_preview=True)

# --- Главная функция ---
async def main():
    # Настройка uvicorn сервера
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    # Параллельно запускаем шедулер, телеграм-бота и API с контролем ошибок
    tasks = [
        asyncio.create_task(start_scheduler(), name="Scheduler"),
        asyncio.create_task(dp.start_polling(bot), name="Telegram Bot"),
        asyncio.create_task(server.serve(), name="API Server"),
    ]
    
    # Wait for any task to fail
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
    
    for task in done:
        if task.exception():
            name = task.get_name()
            err = task.exception()
            print(f"❌ Critical failure in {name}: {err}")
            
    # Terminate others
    for task in pending:
        task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
