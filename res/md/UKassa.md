Как всё будет происходить (end-to-end, по шагам)

### Участники

* **Telegram Bot (aiogram)** — только UI: тарифы, кнопка “Оплатить”, “Проверить”.
* **Backend (FastAPI)** — источник истины: создаёт платежи в ЮKassa, принимает вебхуки, ведёт подписки.
* **ЮKassa** — принимает карту, возвращает `confirmation_url`, присылает статус.

---

## Шаг 0. Пользователь выбирает тариф в боте

1. Пользователь жмёт “Купить” → выбирает “Картой” → выбирает тариф (например, 1 месяц / 3 месяца).
2. Бот делает запрос в backend:

* “Создай заказ и платеж на сумму X для user_id=TG_ID и plan_id=…”

---

## Шаг 1. Backend создаёт платёж в ЮKassa (как в доке на скрине)

Backend делает `Payment.create` (или HTTP-запрос) с параметрами:

* `amount.value = "100.00"`
* `amount.currency = "RUB"`
* `capture = true` (деньги списываются сразу после успешной оплаты)
* `confirmation.type = "redirect"`
* `confirmation.return_url = "https://.../return"` (куда вернётся пользователь после оплаты)
* `description` (до 128 символов)
* `metadata` (очень рекомендую) — кладёте ваши данные:
  * `order_id`
  * `user_id`
  * `plan_id`

 **И обязательно заголовок идемпотентности** : `Idempotence-Key: <uuid>`

### Что возвращает ЮKassa

ЮKassa вернёт объект платежа со статусом `pending` и ссылкой:

* `payment.id` — идентификатор платежа в ЮKassa
* `confirmation.confirmation_url` —  **страница оплаты** , куда нужно отправить пользователя

Backend сохраняет в БД запись платежа (`status=pending`, `yookassa_payment_id=...`, `idempotence_key=...`) и отдаёт боту `confirmation_url`.

---

## Шаг 2. Бот отправляет пользователя на оплату

Бот отправляет сообщение с кнопкой:

* **Inline кнопка (url)** → `confirmation_url`

Пользователь нажимает → открывается страница ЮKassa и вводит данные карты.

---

## Шаг 3. Пользователь оплачивает → статус меняется

После попытки оплаты платеж становится:

* `succeeded` — успешно
* `canceled` — отменён / ошибка / отказался платить

---

## Шаг 4. Как backend узнаёт результат (лучший способ — webhook)

### Вебхук (рекомендуется)

Ты в кабинете ЮKassa указываешь webhook URL:

* `POST https://<твоя_публичная_ссылка>/yookassa/webhook`

ЮKassa **сама** отправит уведомление на твой backend, когда платеж сменит статус.

Backend при получении webhook делает:

1. Берёт `payment.id`, `status`, `metadata.order_id` (или ищет по payment.id).
2. Находит запись в `payments`.
3. Если `status == succeeded`:
   * отмечает `payments.status = succeeded`
   * активирует/продлевает подписку в таблице `subscriptions`
4. Если `status == canceled`:
   * отмечает `payments.status = canceled`

> Вебхук может прийти повторно — обработчик должен быть идемпотентным: если платеж уже `succeeded`, второй раз ничего не делать.

---

## Шаг 5. Что делает return_url (и почему он не заменяет webhook)

`return_url` — это просто куда ЮKassa вернёт пользователя в браузере после оплаты/ошибки.

* Юзер может закрыть страницу и не вернуться
* return_url не гарантирует, что оплата успешна

Поэтому:

* **return_url** — для UX (“Спасибо, возвращайтесь в бот”)
* **webhook** — для бизнес-логики (“Активировать подписку”)

---

## Шаг 6. Проверка оплаты из бота (страховка)

Добавь кнопку “✅ Проверить оплату”.

Когда пользователь нажимает:

1. бот вызывает backend: `GET /payments/{order_id}`
2. backend смотрит в БД статус
3. если всё ещё `pending`, backend может дополнительно спросить ЮKassa по `payment_id` и обновить статус
4. если `succeeded` — бот сообщает “Оплата прошла, подписка активна”.

---

# Важно про “без домена”

Чтобы webhook работал, нужен  **публичный HTTPS URL** .
Можно без покупки домена:

* ngrok
* Cloudflare Tunnel
* временный домен хостинга (Render/Fly/Railway)

Но URL должен быть доступен из интернета.

---

# Таблицы (отдельно)

Ниже минимальный набор таблиц, который хорошо подходит именно под  **VPN подписки** .

## 1) users

Храним минимум по пользователю Telegram.

**users**

* `id` BIGINT PK — Telegram user id
* `created_at` TIMESTAMP
* `username` TEXT NULL
* `first_name` TEXT NULL

## 2) plans (по желанию, но удобно)

Справочник тарифов, чтобы не хардкодить.

**plans**

* `id` TEXT PK (например: `m1`, `m3`, `y1`)
* `title` TEXT
* `duration_days` INT (или `duration_months`)
* `price_rub` NUMERIC(10,2)
* `is_active` BOOL

Можно без таблицы plans — хранить в конфиге, но таблица удобнее.

## 3) payments (важнейшая)

**payments**

* `id` UUID PK — ваш order/payment id
* `user_id` BIGINT FK -> users.id
* `plan_id` TEXT (FK -> plans.id или просто строка)
* `amount` NUMERIC(10,2)
* `currency` TEXT (обычно RUB)
* `status` TEXT (`pending` / `succeeded` / `canceled`)
* `yookassa_payment_id` TEXT UNIQUE
* `idempotence_key` TEXT UNIQUE
* `confirmation_url` TEXT NULL (можно хранить для логов)
* `created_at` TIMESTAMP
* `updated_at` TIMESTAMP
* `paid_at` TIMESTAMP NULL
* `canceled_at` TIMESTAMP NULL

## 4) subscriptions (активная подписка)

**subscriptions**

* `id` UUID PK
* `user_id` BIGINT FK -> users.id UNIQUE (если одна подписка на пользователя)
* `plan_id` TEXT
* `status` TEXT (`active` / `expired`)
* `active_until` TIMESTAMP
* `created_at` TIMESTAMP
* `updated_at` TIMESTAMP

### Логика продления

* Если подписка активна и `active_until > now`:
  * продляем от `active_until`
* иначе:
  * начинаем от `now`

## 5) webhook_events (не обязательно, но полезно)

Чтобы дебажить и обеспечивать идемпотентность.

**webhook_events**

* `id` UUID PK
* `event_id` TEXT UNIQUE NULL (если ЮKassa присылает id события)
* `payment_id` TEXT (yookassa_payment_id)
* `status` TEXT
* `raw_json` JSONB
* `received_at` TIMESTAMP
