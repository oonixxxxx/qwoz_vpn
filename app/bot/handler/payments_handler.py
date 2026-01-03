from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from app.bot.keyboard.buy_keyboard import BuyMenuCb, buy_menu_keyboard
from app.bot.keyboard.main_menu import main_menu_keyboard, StartMenuCb

payments_router = Router()


@payments_router.callback_query(StartMenuCb.filter(F.action == "buy"))
async def on_buy(callback: CallbackQuery, callback_data: StartMenuCb):
    await callback.answer()

    try:
        await callback.message.edit_text(
            "🛒 Выберите способ оплаты:",
            reply_markup=buy_menu_keyboard(),
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer("Меню оплаты уже открыто", show_alert=False)
        else:
            raise


@payments_router.callback_query(BuyMenuCb.filter(F.action == "crypto"))
async def pay_crypto(callback: CallbackQuery, callback_data: BuyMenuCb):
    """
    Заглушка для оплаты криптовалютой.
    Реальная логика оплаты / выдачи доступа будет добавлена позже.
    """
    await callback.answer()

    await callback.message.edit_text(
        "💰 Вы выбрали оплату криптовалютой.\n\n"
        "Оплата и выдача доступа будут реализованы позже.",
        reply_markup=buy_menu_keyboard(),
    )


@payments_router.callback_query(BuyMenuCb.filter(F.action == "card"))
async def pay_card(callback: CallbackQuery, callback_data: BuyMenuCb):
    """
    Заглушка для оплаты картой.
    """
    await callback.answer()

    await callback.message.edit_text(
        "💳 Вы выбрали оплату картой.\n\n"
        "Оплата и выдача доступа будут реализованы позже.",
        reply_markup=buy_menu_keyboard(),
    )


@payments_router.callback_query(BuyMenuCb.filter(F.action == "cancel"))
async def pay_cancel(callback: CallbackQuery, callback_data: BuyMenuCb):
    await callback.answer("Отменено")

    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=main_menu_keyboard(),
    )
