from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
import httpx

from app.bot.keyboard.buy_keyboard import BuyMenuCb, buy_menu_keyboard
from app.bot.keyboard.main_menu import main_menu_keyboard, StartMenuCb
from app.bot.services.instructions import format_instruction
from app.bot.services.qr import build_qr_image
from app.bot.services.xray_api import XrayAPIClient

# Роутер — “контейнер” для хендлеров (обработчиков) событий/коллбеков.
# Его потом подключают в общий Dispatcher/Router бота.
payments_router = Router()

# Клиент для общения с вашим сервером/панелью (условно: Xray/VLESS backend),
# который умеет “выдавать доступ” пользователю (создавать конфиг/учётку).
api_client = XrayAPIClient()


@payments_router.callback_query(StartMenuCb.filter(F.action == "buy"))
async def on_buy(callback: CallbackQuery, callback_data: StartMenuCb):
    """
    Хендлер нажатия кнопки “Купить” в главном меню.

    Что делает:
    1) Подтверждает Telegram'у, что коллбек обработан (callback.answer()).
       Иначе у пользователя будет крутиться “часики”.
    2) Пытается обновить текст сообщения и показать подменю способов оплаты
       (Crypto / Card / Cancel).
    3) Если пользователь нажал “Купить” повторно и текст/клавиатура не меняются,
       Telegram вернёт ошибку "message is not modified" — мы её ловим и
       просто показываем короткий ответ без ошибки.
    """
    await callback.answer()

    try:
        await callback.message.edit_text(
            "🛒 Выберите способ оплаты:",
            reply_markup=buy_menu_keyboard(),  # inline-кнопки: Crypto / Card / Cancel
        )
    except TelegramBadRequest as e:
        # Telegram ругается, если редактируем сообщение тем же самым текстом/markup.
        if "message is not modified" in str(e):
            await callback.answer("Меню оплаты уже открыто", show_alert=False)
        else:
            # Если это другая ошибка — не скрываем, пусть упадёт и вы увидите проблему.
            raise


@payments_router.callback_query(BuyMenuCb.filter(F.action == "crypto"))
async def pay_crypto(callback: CallbackQuery, callback_data: BuyMenuCb):
    """
    Хендлер нажатия “Crypto”.

    Логика в текущем коде такая:
    - Считаем, что “оплата криптой подтверждена” (по факту тут нет реальной проверки платежа).
    - Вызываем backend (api_client.provision_user), чтобы:
        * создать пользователю VPN-доступ / выдать VLESS ссылку
        * вернуть данные (vless_url, expires_at и т.п.)
    - Если backend недоступен/упал — показываем ошибку и оставляем меню оплаты.
    - Если успех:
        * редактируем исходное сообщение: “оплата подтверждена”
        * отправляем отдельным сообщением QR-код и инструкцию подключения
    """
    await callback.answer()  # убираем “часики”

    # Telegram user_id — используем как идентификатор клиента в вашей системе.
    user_id = callback.from_user.id

    try:
        # provision_user — ваш API-вызов на сервер (через httpx внутри XrayAPIClient).
        # Должен вернуть payload вида:
        # {
        #   "vless_url": "...",
        #   "expires_at": "..." (может быть None/отсутствовать)
        # }
        payload = await api_client.provision_user(user_id)
    except httpx.HTTPError:
        # Любая HTTP/network ошибка при обращении к backend.
        await callback.message.edit_text(
            "⚠️ Не удалось подтвердить оплату. Попробуйте позже.",
            reply_markup=buy_menu_keyboard(),
        )
        return

    # Сообщаем в “текущем” сообщении, что успех (и оставляем клавиатуру оплаты).
    await callback.message.edit_text(
        "💰 Оплата криптовалютой подтверждена.",
        reply_markup=buy_menu_keyboard(),
    )

    # Генерируем QR-картинку из VLESS-ссылки.
    # build_qr_image обычно возвращает файл/байты, совместимые с answer_photo.
    qr_image = build_qr_image(payload["vless_url"])

    # Отправляем пользователю новое сообщение с фото (QR) + текст-инструкцию.
    await callback.message.answer_photo(
        qr_image,
        caption=format_instruction(payload["vless_url"], payload.get("expires_at")),
    )


@payments_router.callback_query(BuyMenuCb.filter(F.action == "card"))
async def pay_card(callback: CallbackQuery, callback_data: BuyMenuCb):
    """
    Хендлер нажатия “Card”.

    Сейчас он практически полностью копирует pay_crypto, только текст другой:
    - Выдаёт доступ через provision_user
    - При ошибке — показывает предупреждение
    - При успехе — пишет “оплата картой подтверждена” + отправляет QR и инструкцию

    В реальном проекте обычно сюда добавляют:
    - создание invoice / ссылку на оплату
    - вебхук/проверку платежа
    - только ПОСЛЕ подтверждения платежа — provision_user()
    """
    await callback.answer()
    user_id = callback.from_user.id

    try:
        payload = await api_client.provision_user(user_id)
    except httpx.HTTPError:
        await callback.message.edit_text(
            "⚠️ Не удалось подтвердить оплату. Попробуйте позже.",
            reply_markup=buy_menu_keyboard(),
        )
        return

    await callback.message.edit_text(
        "💳 Оплата картой подтверждена.",
        reply_markup=buy_menu_keyboard(),
    )

    qr_image = build_qr_image(payload["vless_url"])
    await callback.message.answer_photo(
        qr_image,
        caption=format_instruction(payload["vless_url"], payload.get("expires_at")),
    )


@payments_router.callback_query(BuyMenuCb.filter(F.action == "cancel"))
async def pay_cancel(callback: CallbackQuery, callback_data: BuyMenuCb):
    """
    Хендлер нажатия “Cancel”.

    - Отвечаем на коллбек “Отменено”
    - Редактируем текущее сообщение и возвращаем главное меню (клавиатуру main menu)
    """
    await callback.answer("Отменено")
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=main_menu_keyboard(),
    )
