# Полное руководство по API ЮKassa

## 📋 Введение

**ЮKassa** — это универсальный REST API для обработки онлайн-платежей и выплат. API работает с реальными объектами (платежами, возвратами, выплатами) и предоставляет предсказуемые HTTP-ответы.

## 🌐 Базовые принципы

### 1. Технические характеристики

- **Базовый URL:** `https://api.yookassa.ru/v3/`
- **Протокол:** HTTPS
- **Поддерживаемые методы:**
  - `POST` — создание объектов (платежи, возвраты)
  - `GET` — получение информации
  - `DELETE` — отмена операций
- **Формат данных:** JSON для всех ответов и POST-запросов
- **Кодировка:** UTF-8

### 2. Структура запросов

#### POST-запросы:

```
POST /v3/{ресурс}
Content-Type: application/json
Authorization: Basic {base64_credentials}
Idempotence-Key: {unique_key}

{
  "параметр": "значение",
  ...
}
```

#### GET-запросы:

```
GET /v3/{ресурс}/{id}
Authorization: Basic {base64_credentials}
```

## 🔐 Аутентификация

### HTTP Basic Auth (основной метод)

Для каждого запроса требуется передавать в заголовке `Authorization` данные аутентификации:

```python
import base64
import requests

# Ваши учетные данные
shop_id = "ваш_shopId"
secret_key = "ваш_секретный_ключ"

# Создание заголовка Authorization вручную
credentials = f"{shop_id}:{secret_key}"
base64_credentials = base64.b64encode(credentials.encode()).decode()
headers = {
    "Authorization": f"Basic {base64_credentials}",
    "Content-Type": "application/json",
    "Idempotence-Key": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Или используйте встроенную поддержку requests:**

```python
response = requests.post(
    url,
    auth=(shop_id, secret_key),  # Библиотека сама создаст заголовок
    headers=headers,
    json=data
)
```

### Где получить учетные данные:

#### Для приема платежей:

1. **Идентификатор магазина (shopId):**

   - Личный кабинет → Настройки → Магазин → `shopId`
2. **Секретный ключ:**

   - Личный кабинет → Интеграция → Ключи API
   - Для реального магазина: требуется генерация и активация через SMS
   - Для тестового магазина: ключ доступен сразу

#### Для выплат:

1. **Идентификатор шлюза (agentId):**

   - Личный кабинет → Настройки выплат → `agentId`
2. **Секретный ключ:**

   - Тот же раздел "Ключи API"
   - Разные ключи для тестового и реального шлюза

### OAuth 2.0 (для партнеров)

Если вы участвуете в партнерской программе:

```python
headers = {
    "Authorization": "Bearer {ваш_oauth_токен}",
    "Content-Type": "application/json"
}
```

**Важно:** OAuth-токен дает право выполнять финансовые операции. Храните его безопасно!

## ⚙️ Идемпотентность

### Что такое идемпотентность?

Повторный запрос с одинаковыми параметрами и ключом идемпотентности возвращает тот же результат, что и первый запрос. Это защищает от дублирования транзакций при сбоях сети.

### Правила использования:

1. **Когда передавать:**

   - Для всех `POST` и `DELETE` запросов
   - Не требуется для `GET` (и так идемпотентны по природе)
2. **Требования к ключу:**

   - Уникальный для каждой операции
   - Максимум 64 символа
   - Рекомендуется использовать UUID версии 4
3. **Срок действия:** 24 часа с момента первого запроса

### Пример с идемпотентностью:

```python
import uuid
import requests

def create_payment(amount, description):
    url = "https://api.yookassa.ru/v3/payments"
    headers = {
        "Idempotence-Key": str(uuid.uuid4()),  # Генерируем новый UUID для каждого запроса
        "Content-Type": "application/json"
    }
  
    data = {
        "amount": {
            "value": str(amount),
            "currency": "RUB"
        },
        "description": description
    }
  
    response = requests.post(
        url,
        auth=(SHOP_ID, SECRET_KEY),
        headers=headers,
        json=data
    )
  
    return response.json()

# При сетевом сбое можно безопасно повторить:
try:
    result = create_payment(100.00, "Заказ #1")
except requests.exceptions.ConnectionError:
    # Пробуем снова с ТЕМ ЖЕ ключом идемпотентности
    result = create_payment(100.00, "Заказ #1")  # Безопасно!
```

## 💳 Основные объекты API

### 1. Платеж (Payment)

**Создание платежа:**

```python
payment_data = {
    "amount": {
        "value": "1500.50",
        "currency": "RUB"
    },
    "payment_method_data": {
        "type": "bank_card",
        "card": {
            "number": "555555******5599",
            "expiry_year": "2025",
            "expiry_month": "12",
            "csc": "123"
        }
    },
    "confirmation": {
        "type": "redirect",  # или "embedded", "qr", "external"
        "return_url": "https://shop.ru/thank-you"
    },
    "description": "Покупка ноутбука",
    "metadata": {
        "order_id": "12345",
        "customer_id": "user678"
    },
    "receipt": {
        "customer": {
            "email": "customer@email.ru"
        },
        "items": [
            {
                "description": "Ноутбук",
                "quantity": "1",
                "amount": {
                    "value": "1500.50",
                    "currency": "RUB"
                },
                "vat_code": 2,
                "payment_mode": "full_payment",
                "payment_subject": "commodity"
            }
        ]
    }
}
```

**Получение информации о платеже:**

```python
def get_payment(payment_id):
    url = f"https://api.yookassa.ru/v3/payments/{payment_id}"
    response = requests.get(url, auth=(SHOP_ID, SECRET_KEY))
    return response.json()

# Пример ответа:
# {
#   "id": "22d6d597-000f-5000-9000-145f6df21d6f",
#   "status": "waiting_for_capture",
#   "amount": {"value": "1500.50", "currency": "RUB"},
#   "description": "Покупка ноутбука",
#   "recipient": {...},
#   "created_at": "2024-01-15T14:26:00Z",
#   "expires_at": "2024-01-18T14:26:00Z"
# }
```

### 2. Возврат (Refund)

**Создание возврата:**

```python
def create_refund(payment_id, amount):
    url = "https://api.yookassa.ru/v3/refunds"
    headers = {
        "Idempotence-Key": str(uuid.uuid4()),
        "Content-Type": "application/json"
    }
  
    data = {
        "payment_id": payment_id,
        "amount": {
            "value": str(amount),
            "currency": "RUB"
        }
    }
  
    response = requests.post(
        url,
        auth=(SHOP_ID, SECRET_KEY),
        headers=headers,
        json=data
    )
  
    return response.json()
```

### 3. Чек (Receipt)

**Отправка чека:**

```python
receipt_data = {
    "type": "payment",  # или "refund"
    "payment_id": "22d6d597-000f-5000-9000-145f6df21d6f",
    "customer": {
        "email": "customer@email.ru",
        "phone": "79111234567"
    },
    "items": [
        {
            "description": "Ноутбук",
            "quantity": "1.00",
            "amount": {
                "value": "1500.50",
                "currency": "RUB"
            },
            "vat_code": 1,
            "payment_mode": "full_payment",
            "payment_subject": "commodity"
        }
    ],
    "tax_system_code": 1
}
```

## 🔄 Обработка ответов

### Статусы HTTP

| Код | Значение                           | Действия                                 |
| ------ | ------------------------------------------ | ------------------------------------------------ |
| 200    | Успешно                             | Обработать ответ                  |
| 201    | Создано                             | Получить созданный объект |
| 400    | Неверный запрос              | Проверить параметры            |
| 401    | Не авторизован                | Проверить учетные данные   |
| 403    | Доступ запрещен              | Проверить права доступа     |
| 404    | Не найдено                        | Проверить идентификатор    |
| 429    | Слишком много запросов | Уменьшить частоту                |
| 500    | Ошибка сервера                | Проверить статус операции |

### Обработка ошибок 500

При получении HTTP 500:

1. **Не повторяйте запрос сразу** с новым ключом идемпотентности
2. **Запросите статус операции** через GET-запрос
3. **Только после получения статуса** принимайте решение

```python
def safe_operation(operation_func, *args):
    """Безопасное выполнение операции с обработкой ошибок 500"""
    try:
        result = operation_func(*args)
        return result
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 500:
            # Запрашиваем статус оригинальной операции
            operation_id = extract_operation_id(e.response)  # Ваша логика извлечения ID
            status = check_operation_status(operation_id)
          
            if status == "pending":
                # Можно повторить с тем же ключом идемпотентности
                return operation_func(*args)
            elif status == "succeeded":
                return {"status": "already_completed"}
            else:
                raise Exception(f"Operation failed with status: {status}")
        else:
            raise

def check_operation_status(operation_id):
    """Проверка статуса операции после ошибки 500"""
    # Определите тип операции (платеж, возврат) и сделайте GET-запрос
    pass
```

## 📊 Сценарии использования

### 1. Одностадийная оплата

```python
def simple_payment(amount, order_id, email):
    """Создание и немедленное подтверждение платежа"""
    payment = create_payment({
        "amount": {"value": amount, "currency": "RUB"},
        "payment_method_data": {"type": "bank_card"},
        "confirmation": {"type": "redirect", "return_url": "https://shop.ru/thanks"},
        "capture": True,  # Немедленное списание
        "description": f"Заказ #{order_id}",
        "metadata": {"order_id": order_id},
        "receipt": {
            "customer": {"email": email},
            "items": [...]
        }
    })
  
    if payment["status"] == "succeeded":
        # Платёж успешно проведён
        fulfill_order(order_id)
  
    return payment["confirmation"]["confirmation_url"]
```

### 2. Двухстадийная оплата (холдирование)

```python
def two_stage_payment(amount, order_id):
    """Создание с последующим подтверждением"""
    # 1. Создание платежа с capture=False
    payment = create_payment({
        "amount": {"value": amount, "currency": "RUB"},
        "capture": False,  # Только резервирование
        "description": f"Заказ #{order_id}",
        "expires_at": (datetime.now() + timedelta(days=1)).isoformat()
    })
  
    # 2. Пользователь подтверждает платеж
    # 3. Подтверждение (списание) в течение срока холдирования
    if payment["status"] == "waiting_for_capture":
        capture_payment(payment["id"], amount)

def capture_payment(payment_id, amount):
    """Подтверждение (списание) платежа"""
    url = f"https://api.yookassa.ru/v3/payments/{payment_id}/capture"
    headers = {"Idempotence-Key": str(uuid.uuid4())}
  
    data = {"amount": {"value": str(amount), "currency": "RUB"}}
  
    response = requests.post(
        url,
        auth=(SHOP_ID, SECRET_KEY),
        headers=headers,
        json=data
    )
  
    return response.json()
```

### 3. Подписки (сохраненные платежные данные)

```python
def create_subscription(customer_id, card_data):
    """Сохранение карты для повторных списаний"""
    payment = create_payment({
        "amount": {"value": "1.00", "currency": "RUB"},  # Сумма для проверки
        "payment_method_data": {"type": "bank_card", "card": card_data},
        "save_payment_method": True,  # Сохранить для повторного использования
        "capture": True,
        "description": "Привязка карты для подписки",
        "metadata": {"customer_id": customer_id}
    })
  
    if payment["status"] == "succeeded":
        saved_payment_method_id = payment["payment_method"]["id"]
        save_to_database(customer_id, saved_payment_method_id)
  
    return payment
```

### 4. Выплаты

```python
def create_payout(amount, payout_token, description):
    """Создание выплаты"""
    url = "https://api.yookassa.ru/v3/payouts"
    headers = {"Idempotence-Key": str(uuid.uuid4())}
  
    data = {
        "amount": {"value": str(amount), "currency": "RUB"},
        "payout_destination_data": {
            "type": "bank_card",
            "card": {
                "number": payout_token  # Токен карты получателя
            }
        },
        "description": description,
        "metadata": {"purpose": "cashback"}
    }
  
    response = requests.post(
        url,
        auth=(AGENT_ID, SECRET_KEY),  # Учетные данные шлюза выплат!
        headers=headers,
        json=data
    )
  
    return response.json()
```

## 🛠️ Лучшие практики и рекомендации

### 1. Безопасность

```python
# НЕПРАВИЛЬНО - ключи в коде
SECRET_KEY = "live_abcdef123456"

# ПРАВИЛЬНО - ключи из переменных окружения
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
```

### 2. Обработка вебхуков (уведомлений)

```python
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

@app.route('/webhook/yookassa', methods=['POST'])
def webhook():
    # Проверка подписи
    signature = request.headers.get('Yookassa-Signature')
    body = request.get_data(as_text=True)
  
    # Секрет для проверки подписи (отдельный от API-ключа)
    secret = os.getenv("YOOKASSA_WEBHOOK_SECRET")
  
    # Проверка HMAC-SHA256
    expected_signature = hmac.new(
        secret.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()
  
    if not hmac.compare_digest(signature, expected_signature):
        return jsonify({"error": "Invalid signature"}), 401
  
    event = request.json
    event_type = event["event"]
    object_data = event["object"]
  
    # Обработка разных типов событий
    handlers = {
        "payment.succeeded": handle_payment_succeeded,
        "payment.waiting_for_capture": handle_payment_waiting,
        "payment.canceled": handle_payment_canceled,
        "refund.succeeded": handle_refund_succeeded
    }
  
    handler = handlers.get(event_type)
    if handler:
        handler(object_data)
  
    return jsonify({"status": "ok"})

def handle_payment_succeeded(payment):
    order_id = payment["metadata"]["order_id"]
    fulfill_order(order_id)
    send_email_notification(payment)
```

### 3. Логирование и мониторинг

```python
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('yookassa_api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def log_api_call(method, endpoint, data, response):
    """Логирование всех вызовов API"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "method": method,
        "endpoint": endpoint,
        "request_data": data,
        "response_status": response.status_code,
        "response_data": response.json() if response.content else None
    }
  
    logger.info(json.dumps(log_entry))
  
    # Дополнительно: сохранение в базу для аналитики
    save_to_audit_log(log_entry)
```

### 4. Обработка таймаутов и повторных попыток

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests.exceptions

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(
        (requests.exceptions.ConnectionError,
         requests.exceptions.Timeout,
         requests.exceptions.HTTPError)
    )
)
def make_api_request(url, method="GET", data=None, headers=None):
    """Устойчивый запрос с повторными попытками"""
    response = requests.request(
        method=method,
        url=url,
        json=data,
        headers=headers,
        auth=(SHOP_ID, SECRET_KEY),
        timeout=(3.05, 27)  # (connect timeout, read timeout)
    )
  
    response.raise_for_status()
    return response
```

## 🧪 Тестирование

### Тестовые данные

```python
# Тестовый магазин
TEST_SHOP_ID = "ваш_test_shopId"
TEST_SECRET_KEY = "test_ваш_ключ"

# Тестовые карты
TEST_CARDS = {
    "success": "5555555555554477",  # Успешный платеж
    "3ds_required": "5555555555555599",  # Требуется 3DS
    "insufficient_funds": "5555555555555542",  # Недостаточно средств
    "expired": "5555555555555513",  # Просроченная карта
    "rejected": "5555555555555521"  # Отклонена
}

# Специальные суммы для тестовых сценариев
TEST_AMOUNTS = {
    "success": "100.00",
    "failure": "200.00",  # Всегда приводит к ошибке
    "random": "300.00"  # Случайный результат
}
```

### Интеграционные тесты

```python
import unittest

class TestYooKassaAPI(unittest.TestCase):
  
    def setUp(self):
        self.shop_id = TEST_SHOP_ID
        self.secret_key = TEST_SECRET_KEY
      
    def test_payment_creation(self):
        """Тест создания платежа"""
        payment = create_payment({
            "amount": {"value": "100.00", "currency": "RUB"},
            "payment_method_data": {"type": "bank_card"},
            "confirmation": {"type": "redirect"},
            "capture": True,
            "description": "Тестовый платеж"
        })
      
        self.assertIn("id", payment)
        self.assertIn("status", payment)
        self.assertEqual(payment["amount"]["value"], "100.00")
      
    def test_idempotency(self):
        """Тест идемпотентности"""
        key = str(uuid.uuid4())
      
        # Первый запрос
        payment1 = create_payment_with_key(key, {...})
        # Второй запрос с тем же ключом
        payment2 = create_payment_with_key(key, {...})
      
        self.assertEqual(payment1["id"], payment2["id"])
      
    def test_error_handling(self):
        """Тест обработки ошибок"""
        with self.assertRaises(requests.exceptions.HTTPError):
            create_payment({
                "amount": {"value": "invalid", "currency": "RUB"},
                # Некорректные данные
            })
```

## 📈 Мониторинг и аналитика

### Ключевые метрики для отслеживания

```python
class YooKassaMetrics:
    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_payments": 0,
            "failed_payments": 0,
            "avg_response_time": 0,
            "error_codes": {}
        }
  
    def track_request(self, endpoint, duration, status_code):
        self.metrics["total_requests"] += 1
      
        if 200 <= status_code < 300:
            if "payments" in endpoint and "capture" not in endpoint:
                self.metrics["successful_payments"] += 1
        else:
            self.metrics["failed_payments"] += 1
            self.metrics["error_codes"][status_code] = \
                self.metrics["error_codes"].get(status_code, 0) + 1
      
        # Расчет среднего времени ответа
        total_time = self.metrics["avg_response_time"] * (self.metrics["total_requests"] - 1)
        self.metrics["avg_response_time"] = (total_time + duration) / self.metrics["total_requests"]
  
    def get_report(self):
        success_rate = (self.metrics["successful_payments"] / 
                       max(self.metrics["total_requests"], 1)) * 100
        return {
            **self.metrics,
            "success_rate_percent": round(success_rate, 2)
        }
```

## 🔗 Полезные ссылки и ресурсы

1. **Полная документация:** https://yookassa.ru/developers
2. **Справка API:** https://yookassa.ru/developers/api
3. **Готовые SDK:**
   - **Python:** `pip install yookassa`
   - **PHP:** `composer require yoomoney/yookassa-sdk-php`
   - **Java:** https://github.com/yoomoney/yookassa-sdk-java
4. **Тестовые данные и симулятор:** https://yookassa.ru/developers/testing
5. **Поддержка:** https://yookassa.ru/help

## 🚀 Быстрый старт

1. **Регистрация:**

   ```bash
   # 1. Зарегистрируйтесь на yookassa.ru
   # 2. Создайте тестовый магазин
   # 3. Получите shopId и секретный ключ
   ```
2. **Установка SDK:**

   ```bash
   pip install yookassa
   ```
3. **Минимальный рабочий пример:**

   ```python
   from yookassa import Configuration, Payment

   # Настройка
   Configuration.account_id = 'ваш_shopId'
   Configuration.secret_key = 'ваш_секретный_ключ'

   # Создание платежа
   payment = Payment.create({
       "amount": {"value": "100.00", "currency": "RUB"},
       "payment_method_data": {"type": "bank_card"},
       "confirmation": {"type": "redirect", "return_url": "https://shop.ru/thanks"},
       "description": "Тестовый заказ"
   })

   print(payment.confirmation.confirmation_url)
   ```

## ⚠️ Частые ошибки и их решение

| Ошибка              | Причина                                 | Решение                                   |
| ------------------------- | ---------------------------------------------- | ------------------------------------------------ |
| `401 Unauthorized`      | Неверные учетные данные   | Проверить shopId/secret_key             |
| `400 Invalid request`   | Некорректные параметры    | Проверить формат JSON             |
| `404 Not found`         | Несуществующий ресурс      | Проверить ID объекта             |
| `429 Too many requests` | Превышен лимит запросов   | Увеличить интервалы            |
| `500 Internal error`    | Временная ошибка сервера | Проверить статус операции |

Это полное руководство покрывает все основные аспекты работы с API ЮKassa. Начинайте с тестового режима, тщательно тестируйте все сценарии и всегда используйте идемпотентность для POST/DELETE запросов.
