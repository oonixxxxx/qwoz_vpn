from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData


class BuyMenuCb(CallbackData, prefix="buy_menu"):
    action: str  # crypto | card | cancel


def buy_menu_keyboard():
    kb = InlineKeyboardBuilder()

    kb.button(
        text="💰 Оплатить криптовалютой",
        callback_data=BuyMenuCb(action="crypto").pack(),
    )

    kb.button(
        text="💳 Оплатить картой",
        callback_data=BuyMenuCb(action="card").pack(),
    )

    kb.button(
        text="❌ Отмена",
        callback_data=BuyMenuCb(action="cancel").pack(),
    )

    kb.adjust(1)
    return kb.as_markup()
