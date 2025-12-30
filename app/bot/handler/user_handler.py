from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

import httpx

from app.bot.data.config import ADMIN_TELEGRAM_IDS, SUPPORT_USERNAME
from app.bot.keyboard.main_menu import main_menu_keyboard, StartMenuCb
from app.bot.services.instructions import format_instruction
from app.bot.services.qr import build_qr_image
from app.bot.services.xray_api import XrayAPIClient

user_router = Router()
api_client = XrayAPIClient()


@user_router.message(CommandStart())
async def send_welcome(message: Message):
    await message.answer(
        "Welcome! I'm here to help you. Use the menu below to navigate.",
        reply_markup=main_menu_keyboard()
    )


@user_router.callback_query(StartMenuCb.filter(F.action == "profile"))
async def on_profile(callback: CallbackQuery, callback_data: StartMenuCb):
    await callback.answer()
    profile_text = f"👤 Профиль\n\nВаш ID: {callback.from_user.id}"
    try:
        user = await api_client.get_user(callback.from_user.id)
    except httpx.HTTPError:
        user = None

    if user:
        profile_text += f"\nСтатус: {user['status']}"

    await callback.message.edit_text(
        profile_text,
        reply_markup=main_menu_keyboard()
    )


@user_router.callback_query(StartMenuCb.filter(F.action == "support"))
async def on_support(callback: CallbackQuery, callback_data: StartMenuCb):
    await callback.answer()
    await callback.message.edit_text(
        "🧑‍💻 Техподдержка\n\n"
        "Опишите проблему одним сообщением или напишите сюда:\n"
        f"https://t.me/{SUPPORT_USERNAME}",
        reply_markup=main_menu_keyboard()
    )


@user_router.callback_query(StartMenuCb.filter(F.action == "howto"))
async def on_howto(callback: CallbackQuery, callback_data: StartMenuCb):
    await callback.answer()
    await callback.message.edit_text(
        "📖 Как пользоваться\n\n"
        "1) Нажмите «Купить» и оплатите подписку.\n"
        "2) Получите доступ в разделе «Мой ключ».\n"
        "3) Отсканируйте QR или вставьте ссылку в клиент.\n"
        "4) Готово ✅",
        reply_markup=main_menu_keyboard()
    )


@user_router.callback_query(StartMenuCb.filter(F.action == "config"))
async def on_config(callback: CallbackQuery, callback_data: StartMenuCb):
    await callback.answer()
    await _send_config(callback.message, callback.from_user.id)


@user_router.message(Command("help"))
async def help_message(message: Message):
    await message.answer(
        "Here are some commands you can use:\n"
        "/start - Start the bot\n"
        "/help - Show this help message"
    )


@user_router.message(Command("config"))
async def config_message(message: Message):
    await _send_config(message, message.from_user.id)


@user_router.message(Command("revoke"))
async def revoke_user(message: Message):
    if message.from_user.id not in ADMIN_TELEGRAM_IDS:
        await message.answer("Недостаточно прав для отзыва доступа.")
        return

    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Использование: /revoke <telegram_id>")
        return

    telegram_id = int(parts[1])
    try:
        payload = await api_client.revoke_user(telegram_id)
    except httpx.HTTPError:
        await message.answer("Не удалось отозвать доступ. Проверьте API.")
        return

    await message.answer(
        f"Доступ для {payload['telegram_id']} отозван.",
    )


async def _send_config(message: Message, telegram_id: int) -> None:
    try:
        payload = await api_client.get_user_config(telegram_id)
    except httpx.HTTPError:
        payload = None

    if not payload:
        await message.answer("Нет активной подписки. Нажмите «Купить» для доступа.")
        return

    qr_image = build_qr_image(payload["vless_url"])
    await message.answer_photo(
        qr_image,
        caption=format_instruction(payload["vless_url"], payload.get("expires_at")),
    )
