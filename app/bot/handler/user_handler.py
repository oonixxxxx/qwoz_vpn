from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart

from app.bot.keyboard.main_menu import main_menu_keyboard, StartMenuCb

user_router = Router()

@user_router.message(CommandStart())
async def send_welcome(message: Message):
    await message.answer(
        "Welcome! I'm here to help you. Use the menu below to navigate.",
        reply_markup=main_menu_keyboard()
    )

@user_router.callback_query(StartMenuCb.filter(F.action == "profile"))
async def on_profile(callback: CallbackQuery, callback_data: StartMenuCb):
    await callback.answer()
    await callback.message.edit_text(
        f"👤 Профиль\n\nВаш ID: {callback.from_user.id}",
        reply_markup=main_menu_keyboard()
    )

@user_router.callback_query(StartMenuCb.filter(F.action == "support"))
async def on_support(callback: CallbackQuery, callback_data: StartMenuCb):
    await callback.answer()
    await callback.message.edit_text(
        "🧑‍💻 Техподдержка\n\nОпишите проблему одним сообщением.",
        reply_markup=main_menu_keyboard()
    )

@user_router.callback_query(StartMenuCb.filter(F.action == "howto"))
async def on_howto(callback: CallbackQuery, callback_data: StartMenuCb):
    await callback.answer()
    await callback.message.edit_text(
        "📖 Как пользоваться\n\n1) Нажми «Купить»\n2) Выбери тариф\n3) Оплати\n4) Получи доступ ✅",
        reply_markup=main_menu_keyboard()
    )

@user_router.message(Command("help"))
async def help_message(message: Message):
    await message.answer(
        "Here are some commands you can use:\n"
        "/start - Start the bot\n"
        "/help - Show this help message"
    )