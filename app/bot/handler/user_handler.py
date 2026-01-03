from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from app.bot.data.config import ADMIN_TELEGRAM_IDS, SUPPORT_USERNAME
from app.bot.keyboard.main_menu import main_menu_keyboard, StartMenuCb

# Роутер для пользовательских сценариев
user_router = Router()


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------
@user_router.message(CommandStart())
async def send_welcome(message: Message):
    """
    Команда /start.
    Показывает приветствие и главное меню.
    """
    await message.answer(
        "Welcome! I'm here to help you. Use the menu below to navigate.",
        reply_markup=main_menu_keyboard()
    )


# ---------------------------------------------------------------------------
# Профиль
# ---------------------------------------------------------------------------
@user_router.callback_query(StartMenuCb.filter(F.action == "profile"))
async def on_profile(callback: CallbackQuery, callback_data: StartMenuCb):
    """
    Кнопка «Профиль».

    Сейчас:
    - показывает только Telegram ID пользователя
    - без обращения к backend/API
    """
    await callback.answer()

    profile_text = (
        "👤 Профиль\n\n"
        f"Ваш ID: {callback.from_user.id}\n"
        "Статус: неизвестен"
    )

    await callback.message.edit_text(
        profile_text,
        reply_markup=main_menu_keyboard()
    )


# ---------------------------------------------------------------------------
# Техподдержка
# ---------------------------------------------------------------------------
@user_router.callback_query(StartMenuCb.filter(F.action == "support"))
async def on_support(callback: CallbackQuery, callback_data: StartMenuCb):
    """
    Кнопка «Техподдержка».
    """
    await callback.answer()

    await callback.message.edit_text(
        "🧑‍💻 Техподдержка\n\n"
        "Опишите проблему одним сообщением или напишите сюда:\n"
        f"https://t.me/{SUPPORT_USERNAME}",
        reply_markup=main_menu_keyboard()
    )


# ---------------------------------------------------------------------------
# Как пользоваться
# ---------------------------------------------------------------------------
@user_router.callback_query(StartMenuCb.filter(F.action == "howto"))
async def on_howto(callback: CallbackQuery, callback_data: StartMenuCb):
    """
    Кнопка «Как пользоваться».
    """
    await callback.answer()

    await callback.message.edit_text(
        "📖 Как пользоваться\n\n"
        "1) Нажмите «Купить» и оплатите подписку.\n"
        "2) Получите ключ доступа.\n"
        "3) Добавьте его в VPN-клиент.\n"
        "4) Готово ✅",
        reply_markup=main_menu_keyboard()
    )


# ---------------------------------------------------------------------------
# Конфиг / Мой ключ
# ---------------------------------------------------------------------------
@user_router.callback_query(StartMenuCb.filter(F.action == "config"))
async def on_config(callback: CallbackQuery, callback_data: StartMenuCb):
    """
    Кнопка «Мой ключ».
    Редактирует текущее сообщение (НЕ отправляет новое).
    """
    await callback.answer()

    await callback.message.edit_text(
        _config_text(callback.from_user.id),
        reply_markup=main_menu_keyboard()
    )



# ---------------------------------------------------------------------------
# /help
# ---------------------------------------------------------------------------
@user_router.message(Command("help"))
async def help_message(message: Message):
    """
    Команда /help.
    """
    await message.answer(
        "Available commands:\n"
        "/start — start bot\n"
        "/help — help\n"
        "/config — show config"
    )


# ---------------------------------------------------------------------------
# /config
# ---------------------------------------------------------------------------
@user_router.message(Command("config"))
async def config_message(message: Message):
    """
    Команда /config.
    Делает то же самое, что кнопка «Мой ключ».
    """
    await message.answer(
        _config_text(message.from_user.id),
        reply_markup=main_menu_keyboard()
    )


# ---------------------------------------------------------------------------
# /revoke (админская заглушка)
# ---------------------------------------------------------------------------
@user_router.message(Command("revoke"))
async def revoke_user(message: Message):
    """
    Админская команда /revoke <telegram_id>.

    Сейчас:
    - только проверка прав
    - без реального отзыва доступа
    """
    if message.from_user.id not in ADMIN_TELEGRAM_IDS:
        await message.answer("Недостаточно прав.")
        return

    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Использование: /revoke <telegram_id>")
        return

    telegram_id = parts[1]

    await message.answer(
        f"⚠️ Доступ для пользователя {telegram_id} *условно отозван*.\n"
        "(backend не подключён)",
        parse_mode="Markdown"
    )


# ---------------------------------------------------------------------------
# Вспомогательная функция
# ---------------------------------------------------------------------------
def _config_text(telegram_id: int) -> str:
    """
    Заглушка выдачи VPN-ключа.
    """
    return (
        "🔑 Ваш VPN-ключ\n\n"
        "Подключение будет доступно после оплаты."
    )