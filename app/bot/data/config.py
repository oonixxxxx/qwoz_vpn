import os

BOT_TOKEN = 'your-telegram-bot-token-here'

SUPPORT_USERNAME = ["SUPPORT_USERNAME", "YourSupportUsername"]
#XRAY_API_URL = os.getenv("XRAY_API_URL", "http://localhost:8000")

ADMIN_TELEGRAM_IDS = {
    int(value)
    for value in os.getenv("ADMIN_TELEGRAM_IDS", "").split(",")
    if value.strip().isdigit()
}
