from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

class StartMenuCb(CallbackData, prefix="start_menu"):
    action: str  # profile | buy | support | howto | config

def main_menu_keyboard():
    kb = InlineKeyboardBuilder()

    kb.button(
        text="👤 Профиль",
        callback_data=StartMenuCb(
            action="profile"
        ).pack()
    )

    kb.button(
        text="🛒 Купить",
        callback_data=StartMenuCb(
            action="buy"
        ).pack()
    )

    kb.button(
        text="🔑 Мой ключ",
        callback_data=StartMenuCb(action="config").pack()
    )

    kb.button(
        text="🧑‍💻 Техподдержка",
        callback_data=StartMenuCb(
            action="support"
        ).pack()
    )

    kb.button(
        text="📖 Как пользоваться",
        callback_data=StartMenuCb(action="howto").pack()
    )

    kb.adjust(2, 2, 1)
    return kb.as_markup()
