from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

class StartMenuCb(CallbackData, prefix="start_menu"):
    action: str  # profile | buy | support | howto

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
        text="🧑‍💻 Техподдержка",
        url="https://t.me/YourSupportUsername"
    )

    kb.button(
        text="📖 Как пользоваться", 
        callback_data=StartMenuCb(action="howto").pack()
    )

    kb.adjust(2, 2)
    return kb.as_markup()