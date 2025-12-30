# Подробное руководство по интеграции ЮKassa в Telegram-бота

## 📚 **Документация ЮKassa**

- [Основная документация](https://yookassa.ru/developers)
- [API Reference](https://yookassa.ru/developers/api)
- [Создание платежа](https://yookassa.ru/developers/api#create_payment)
- [Вебхуки](https://yookassa.ru/developers/api#webhook)

## 🏗️ **Архитектура платежного процесса**

```
Пользователь → Бот → Ваш сервер → ЮKassa API → Банк
      ↑          ↓         ↑           ↓
      └──────────┴─────────┴───────────┘
        Проверка статуса   Вебхук
```

## 📝 **Полный пример с комментариями**

### Файл `config.py` - конфигурация

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Данные от ЮKassa (получаются в личном кабинете)
    YOOMONEY_SHOP_ID = os.getenv("YOOMONEY_SHOP_ID")
    YOOMONEY_SECRET_KEY = os.getenv("YOOMONEY_SECRET_KEY")
  
    # Тестовые данные (для разработки)
    YOOMONEY_TEST_SHOP_ID = os.getenv("YOOMONEY_TEST_SHOP_ID", "123456")
    YOOMONEY_TEST_SECRET_KEY = os.getenv("YOOMONEY_TEST_SECRET_KEY", "test_abcdefg")
  
    # Режим работы: True - тестовый, False - боевой
    TEST_MODE = os.getenv("TEST_MODE", "True").lower() == "true"
  
    # Ваш бот токен
    BOT_TOKEN = os.getenv("BOT_TOKEN")
  
    # URL для вебхуков
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://yourdomain.com/webhook")
    WEBHOOK_PATH = "/webhook"
  
    @classmethod
    def get_shop_id(cls):
        return cls.YOOMONEY_TEST_SHOP_ID if cls.TEST_MODE else cls.YOOMONEY_SHOP_ID
  
    @classmethod
    def get_secret_key(cls):
        return cls.YOOMONEY_TEST_SECRET_KEY if cls.TEST_MODE else cls.YOOMONEY_SECRET_KEY
```

### Файл `yookassa_client.py` - клиент для работы с API ЮKassa

```python
import aiohttp
import json
import base64
import hashlib
import hmac
from typing import Dict, Any, Optional
from config import Config

class YooKassaClient:
    """
    Асинхронный клиент для работы с API ЮKassa
    Документация: https://yookassa.ru/developers/api
    """
  
    # Базовые URL API
    API_URL = "https://api.yookassa.ru/v3"
    TEST_API_URL = "https://api.yookassa.ru/v3"
  
    def __init__(self):
        self.shop_id = Config.get_shop_id()
        self.secret_key = Config.get_secret_key()
        self.is_test = Config.TEST_MODE
      
        # Базовые заголовки для всех запросов
        auth_string = f"{self.shop_id}:{self.secret_key}"
        self.auth_header = f"Basic {base64.b64encode(auth_string.encode()).decode()}"
  
    def get_base_url(self):
        """Возвращает базовый URL API в зависимости от режима"""
        return self.TEST_API_URL if self.is_test else self.API_URL
  
    async def create_payment(
        self,
        amount: float,
        description: str,
        user_id: int,
        return_url: str
    ) -> Dict[str, Any]:
        """
        Создает платеж в ЮKassa
        Возвращает объект платежа с confirmation_url для редиректа пользователя
      
        Args:
            amount: сумма в рублях (например: 100.50)
            description: описание платежа
            user_id: ID пользователя для сохранения в metadata
            return_url: URL для возврата после оплаты
      
        Returns:
            Dict с данными платежа
        """
      
        # Подготовка данных для запроса
        payment_data = {
            "amount": {
                "value": f"{amount:.2f}",  # Форматируем до 2х знаков после запятой
                "currency": "RUB"
            },
            "payment_method_data": {
                "type": "bank_card"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "capture": True,  # Автоматическое списание средств
            "description": description,
            "metadata": {
                "user_id": user_id,
                "bot_payment": True
            },
            "receipt": {
                "customer": {
                    "email": "user@example.com"  # В реальном боте получать у пользователя
                },
                "items": [
                    {
                        "description": description,
                        "quantity": "1",
                        "amount": {
                            "value": f"{amount:.2f}",
                            "currency": "RUB"
                        },
                        "vat_code": 1,  # НДС 20%
                        "payment_mode": "full_payment",
                        "payment_subject": "service"
                    }
                ]
            }
        }
      
        url = f"{self.get_base_url()}/payments"
        headers = {
            "Authorization": self.auth_header,
            "Idempotence-Key": f"user_{user_id}_{int(time.time())}",  # Уникальный ключ идемпотентности
            "Content-Type": "application/json"
        }
      
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payment_data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    raise Exception(f"Error creating payment: {error_text}")
  
    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Получает статус платежа по ID
      
        Args:
            payment_id: ID платежа в ЮKassa
      
        Returns:
            Dict с данными платежа, включая статус
        """
        url = f"{self.get_base_url()}/payments/{payment_id}"
        headers = {
            "Authorization": self.auth_header,
            "Content-Type": "application/json"
        }
      
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Error getting payment status: {error_text}")
  
    def verify_webhook_signature(self, body: str, signature: str) -> bool:
        """
        Проверяет подпись вебхука от ЮKassa
      
        Args:
            body: тело запроса (строка)
            signature: заголовок "HTTP_CONTENT_SIGNATURE" или "Content-Signature"
      
        Returns:
            True если подпись верна, иначе False
        """
        try:
            # Извлекаем подпись из формата "sha256=..."
            signature_hash = signature.split('=')[1]
          
            # Вычисляем HMAC-SHA256
            digest = hmac.new(
                self.secret_key.encode(),
                body.encode(),
                hashlib.sha256
            ).hexdigest()
          
            # Сравниваем полученную подпись с вычисленной
            return hmac.compare_digest(digest, signature_hash)
          
        except Exception as e:
            print(f"Error verifying signature: {e}")
            return False
  
    async def create_refund(self, payment_id: str, amount: float) -> Dict[str, Any]:
        """
        Создает возврат платежа
      
        Args:
            payment_id: ID оригинального платежа
            amount: сумма возврата
      
        Returns:
            Dict с данными возврата
        """
        refund_data = {
            "payment_id": payment_id,
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            }
        }
      
        url = f"{self.get_base_url()}/refunds"
        headers = {
            "Authorization": self.auth_header,
            "Idempotence-Key": f"refund_{payment_id}_{int(time.time())}",
            "Content-Type": "application/json"
        }
      
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=refund_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Error creating refund: {error_text}")
```

### Файл `bot_payments.py` - основной код бота с платежами

```python
import asyncio
import uuid
import logging
from datetime import datetime
from typing import Dict

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    LabeledPrice
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes,
    MessageHandler,
    filters
)

from yookassa_client import YooKassaClient
from config import Config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация клиента ЮKassa
yookassa = YooKassaClient()

# Временное хранилище платежей (в продакшене используйте БД)
temp_payments: Dict[str, Dict] = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start
    Показывает главное меню с опциями оплаты
    """
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("💰 Купить подписку (100 руб)", callback_data="buy_100")],
        [InlineKeyboardButton("💎 Premium (500 руб)", callback_data="buy_500")],
        [InlineKeyboardButton("📊 Мои платежи", callback_data="my_payments")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
  
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n"
        "Выберите опцию ниже:",
        reply_markup=reply_markup
    )

async def handle_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик нажатия кнопки покупки
    """
    query = update.callback_query
    await query.answer()
  
    user_id = query.from_user.id
    amount = float(query.data.split("_")[1])  # Извлекаем сумму из callback_data
  
    # Генерируем уникальный ID для платежа
    payment_uid = str(uuid.uuid4())[:8]
  
    # Создаем платеж в ЮKassa
    try:
        description = f"Подписка на бота для пользователя {user_id}"
      
        # В реальном приложении return_url должен вести на ваш сайт или специальную страницу
        # Для Telegram бота можно использовать ссылку на бота с deep linking
        return_url = f"https://t.me/{context.bot.username}?start=payment_success"
      
        payment_data = await yookassa.create_payment(
            amount=amount,
            description=description,
            user_id=user_id,
            return_url=return_url
        )
      
        # Сохраняем информацию о платеже во временное хранилище
        temp_payments[payment_uid] = {
            "yookassa_id": payment_data["id"],
            "user_id": user_id,
            "amount": amount,
            "status": payment_data.get("status", "pending"),
            "created_at": datetime.now().isoformat()
        }
      
        # Получаем URL для оплаты
        confirmation_url = payment_data["confirmation"]["confirmation_url"]
      
        # Создаем клавиатуру с кнопкой оплаты
        keyboard = [
            [InlineKeyboardButton("💳 Перейти к оплате", url=confirmation_url)],
            [InlineKeyboardButton("🔄 Проверить статус", callback_data=f"check_{payment_uid}")],
            [InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{payment_uid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
      
        await query.edit_message_text(
            f"💸 *Оплата на сумму {amount} руб.*\n\n"
            f"*ID платежа:* `{payment_uid}`\n"
            f"*Статус:* Ожидает оплаты\n\n"
            "1. Нажмите 'Перейти к оплате'\n"
            "2. Оплатите на странице ЮKassa\n"
            "3. Вернитесь в бот и нажмите 'Проверить статус'\n\n"
            "_Платеж будет автоматически отменен через 30 минут_",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
      
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при создании платежа. Попробуйте позже."
        )

async def check_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Проверяет статус платежа по нажатию кнопки
    """
    query = update.callback_query
    await query.answer()
  
    payment_uid = query.data.split("_")[1]
  
    if payment_uid not in temp_payments:
        await query.edit_message_text("❌ Платеж не найден")
        return
  
    payment_info = temp_payments[payment_uid]
  
    try:
        # Получаем актуальный статус от ЮKassa
        yookassa_data = await yookassa.get_payment_status(payment_info["yookassa_id"])
        current_status = yookassa_data["status"]
      
        # Обновляем статус в хранилище
        temp_payments[payment_uid]["status"] = current_status
      
        status_texts = {
            "pending": "⏳ Ожидает оплаты",
            "waiting_for_capture": "⏳ Ожидает подтверждения",
            "succeeded": "✅ Оплачено успешно",
            "canceled": "❌ Отменено",
            "failed": "❌ Ошибка оплаты"
        }
      
        status_text = status_texts.get(current_status, "Неизвестный статус")
      
        if current_status == "succeeded":
            # Успешная оплата - предоставляем услугу
            await handle_successful_payment(query, payment_info)
          
        elif current_status == "canceled" or current_status == "failed":
            # Платеж отменен или не прошел
            keyboard = [[InlineKeyboardButton("🔄 Попробовать снова", callback_data=f"buy_{int(payment_info['amount'])}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
          
            await query.edit_message_text(
                f"💸 *Платеж {payment_uid}*\n\n"
                f"*Статус:* {status_text}\n"
                f"*Сумма:* {payment_info['amount']} руб.\n\n"
                "Попробуйте оплатить снова или обратитесь в поддержку.",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
          
        else:
            # Платеж еще в процессе
            keyboard = [
                [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_{payment_uid}")],
                [InlineKeyboardButton("💳 Перейти к оплате", url=yookassa_data.get("confirmation", {}).get("confirmation_url", ""))]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
          
            await query.edit_message_text(
                f"💸 *Платеж {payment_uid}*\n\n"
                f"*Статус:* {status_text}\n"
                f"*Сумма:* {payment_info['amount']} руб.\n\n"
                "Если вы уже оплатили, статус обновится в течение минуты.",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
          
    except Exception as e:
        logger.error(f"Error checking payment status: {e}")
        await query.edit_message_text(
            "❌ Ошибка при проверке статуса платежа. Попробуйте позже."
        )

async def handle_successful_payment(query, payment_info):
    """
    Обработка успешного платежа
    Здесь вы предоставляете купленный товар/услугу
    """
    user_id = payment_info["user_id"]
    amount = payment_info["amount"]
  
    # Здесь должна быть ваша логика:
    # 1. Активация подписки в вашей БД
    # 2. Отправка доступа к премиум-функциям
    # 3. Отправка чека на email (если требуется)
  
    keyboard = [[InlineKeyboardButton("🎁 Получить доступ", callback_data="get_access")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
  
    await query.edit_message_text(
        f"🎉 *Оплата прошла успешно!*\n\n"
        f"*Спасибо за покупку!*\n"
        f"*Сумма:* {amount} руб.\n"
        f"*ID платежа:* `{payment_info['yookassa_id']}`\n\n"
        "Доступ к премиум-функциям активирован!\n"
        "Нажмите кнопку ниже, чтобы начать использовать.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
  
    # Отправляем чек (если нужно)
    await send_receipt(query.bot, user_id, payment_info)

async def send_receipt(bot, user_id: int, payment_info: Dict):
    """
    Отправка чека пользователю
    """
    try:
        receipt_text = (
            f"🧾 *Чек об оплате*\n\n"
            f"*Услуга:* Подписка на бота\n"
            f"*Сумма:* {payment_info['amount']} руб.\n"
            f"*Дата:* {payment_info['created_at']}\n"
            f"*ID платежа:* `{payment_info['yookassa_id']}`\n\n"
            f"_Сохраненный чек доступен в личном кабинете ЮKassa_"
        )
      
        await bot.send_message(
            chat_id=user_id,
            text=receipt_text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error sending receipt: {e}")

async def webhook_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик вебхуков от ЮKassa
    ВНИМАНИЕ: Этот обработчик должен быть доступен по HTTPS URL
    """
    # Для вебхуков нужно настроить отдельный endpoint
    # В этом примере используем polling, но для продакшена нужен вебхук
  
    pass

async def setup_webhook_yookassa():
    """
    Настройка вебхука в ЮKassa для получения уведомлений
    """
    webhook_url = f"{Config.WEBHOOK_URL}{Config.WEBHOOK_PATH}"
  
    # Код для настройки вебхука через API ЮKassa
    # Это нужно сделать один раз через личный кабинет или API
  
    logger.info(f"Webhook URL for YooKassa: {webhook_url}")

async def my_payments_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает историю платежей пользователя
    """
    query = update.callback_query
    await query.answer()
  
    user_id = query.from_user.id
  
    # Фильтруем платежи пользователя
    user_payments = [
        p for p in temp_payments.values() 
        if p["user_id"] == user_id
    ]
  
    if not user_payments:
        await query.edit_message_text("📭 У вас еще не было платежей")
        return
  
    payments_text = "📋 *Ваши платежи:*\n\n"
    for idx, payment in enumerate(user_payments[:10], 1):  # Последние 10 платежей
        status_emoji = {
            "succeeded": "✅",
            "pending": "⏳",
            "canceled": "❌",
            "failed": "❌"
        }.get(payment["status"], "❓")
      
        payments_text += (
            f"{idx}. {status_emoji} *{payment['amount']} руб.*\n"
            f"   Статус: {payment['status']}\n"
            f"   Дата: {payment['created_at'][:10]}\n"
            f"   ID: `{payment.get('yookassa_id', 'N/A')[:8]}...`\n\n"
        )
  
    await query.edit_message_text(
        payments_text,
        parse_mode="Markdown"
    )

def main():
    """
    Основная функция запуска бота
    """
    # Создаем Application
    application = Application.builder().token(Config.BOT_TOKEN).build()
  
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("pay", start_command))
  
    # Регистрируем обработчики callback-запросов
    application.add_handler(CallbackQueryHandler(handle_buy_callback, pattern="^buy_"))
    application.add_handler(CallbackQueryHandler(check_payment_status, pattern="^check_"))
    application.add_handler(CallbackQueryHandler(my_payments_handler, pattern="^my_payments"))
  
    # Регистрируем обработчик помощи
    application.add_handler(CallbackQueryHandler(
        lambda u, c: u.callback_query.edit_message_text("❓ Помощь по оплате..."),
        pattern="^help"
    ))
  
    # Запускаем бота
    logger.info("Starting bot...")
  
    if Config.TEST_MODE:
        logger.info("RUNNING IN TEST MODE - payments are simulated")
  
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
```

### Файл `requirements.txt`

```txt
python-telegram-bot==20.7
aiohttp==3.9.1
python-dotenv==1.0.0
```

## 🚀 **Пошаговый план запуска**

### 1. **Регистрация в ЮKassa**

1. Перейдите на [yookassa.ru](https://yookassa.ru)
2. Зарегистрируйтесь как ИП или ООО
3. В личном кабинете:
   - Создайте магазин
   - Получите `shopId` и `secretKey`
   - Настройте способы оплаты
   - Включите тестовый режим

### 2. **Настройка проекта**

```bash
# Создаем виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Устанавливаем зависимости
pip install -r requirements.txt

# Создаем файл .env
YOOMONEY_SHOP_ID="your_shop_id"
YOOMONEY_SECRET_KEY="your_secret_key"
BOT_TOKEN="your_bot_token"
TEST_MODE="True"
```

### 3. **Настройка вебхуков (опционально, но рекомендуется)**

```python
# Через личный кабинет ЮKassa:
# 1. Перейдите в "Настройки" → "Вебхуки"
# 2. Добавьте URL: https://yourdomain.com/yookassa-webhook
# 3. Выберите события: payment.succeeded, payment.canceled

# Или через API:
import requests

webhook_url = "https://yourdomain.com/yookassa-webhook"
response = requests.post(
    "https://api.yookassa.ru/v3/webhooks",
    auth=(shop_id, secret_key),
    json={
        "event": "payment.succeeded",
        "url": webhook_url
    }
)
```

### 4. **Тестирование платежей**

1. **Тестовые карты** от ЮKassa:

   - `5555 5555 5555 4477` - успешная оплата
   - `5555 5555 5555 4495` - отклонена банком
   - CVV: `123`, Дата: `01/30`
2. **Тестовый сценарий**:

   - Пользователь нажимает "Купить подписку"
   - Получает ссылку на оплату
   - Оплачивает тестовой картой
   - Возвращается в бот и проверяет статус
   - Получает доступ к услуге

## 🔐 **Важные моменты безопасности**

### 1. **Хранение секретов**

```python
# НЕПРАВИЛЬНО (в коде):
YOOMONEY_SECRET_KEY = "sk_live_123456789"

# ПРАВИЛЬНО (в .env):
YOOMONEY_SECRET_KEY = os.getenv("YOOMONEY_SECRET_KEY")
```

### 2. **Валидация вебхуков**

```python
async def handle_yookassa_webhook(request):
    # 1. Получаем тело запроса
    body = await request.text()
  
    # 2. Получаем подпись из заголовков
    signature = request.headers.get('Content-Signature')
  
    # 3. Проверяем подпись
    if not yookassa.verify_webhook_signature(body, signature):
        return web.Response(status=403)
  
    # 4. Парсим JSON
    data = json.loads(body)
  
    # 5. Обрабатываем событие
    event = data.get('event')
    payment = data.get('object')
  
    if event == 'payment.succeeded':
        await handle_successful_payment_webhook(payment)
  
    return web.Response(status=200)
```

### 3. **Идемпотентность**

```python
# Всегда используйте уникальный idempotence_key
headers = {
    "Idempotence-Key": f"{user_id}_{int(time.time())}_{uuid.uuid4()}"
}
```

## 📊 **Обработка ошибок**

### Пример обработки типичных ошибок:

```python
async def safe_payment_create(user_id, amount):
    try:
        return await yookassa.create_payment(user_id, amount)
    except aiohttp.ClientError as e:
        logger.error(f"Network error: {e}")
        return {"error": "network_error"}
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return {"error": "server_error"}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": "unexpected_error"}
```

## 🎯 **Продакшен-рекомендации**

### 1. **База данных для платежей**

```python
# models.py
class Payment(Base):
    __tablename__ = 'payments'
  
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    yookassa_id = Column(String)
    amount = Column(Float)
    status = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    metadata = Column(JSON)
```

### 2. **Логирование**

```python
import structlog

logger = structlog.get_logger()

async def log_payment_flow(user_id, action, data):
    logger.info(
        "payment_flow",
        user_id=user_id,
        action=action,
        data=data,
        timestamp=datetime.utcnow().isoformat()
    )
```

### 3. **Мониторинг**

- Настройте алерты на failed платежи
- Отслеживайте среднее время оплаты
- Мониторьте отказы (chargeback rate)

## 📞 **Поддержка**

### Полезные ссылки:

1. [Документация Telegram Bot API](https://core.telegram.org/bots/api)
2. [ЮKassa API Reference](https://yookassa.ru/developers/api)
3. [Python Telegram Bot Documentation](https://python-telegram-bot.org/)

### Для отладки:

```python
# Включите подробное логирование
import logging
logging.basicConfig(level=logging.DEBUG)

# Используйте тестовые данные
YOOMONEY_TEST_SHOP_ID = "your_test_shop_id"
YOOMONEY_TEST_SECRET_KEY = "test_your_test_secret_key"
```

Это полное решение для интеграции оплаты через ЮKassa в Telegram боте. Начните с тестового режима, протестируйте все сценарии, и только потом переходите на боевой режим!
