from __future__ import annotations

from datetime import datetime
from typing import Optional


def format_instruction(vless_url: str, expires_at: Optional[str]) -> str:
    expires_text = "без срока" if not expires_at else _format_expires(expires_at)
    return (
        "✅ Доступ активирован!\n\n"
        f"Ссылка VLESS:\n<code>{vless_url}</code>\n\n"
        f"Срок действия: {expires_text}\n\n"
        "Как подключиться:\n"
        "1) Откройте клиент (Hiddify, v2rayNG, Shadowrocket).\n"
        "2) Добавьте профиль по QR или вставьте ссылку.\n"
        "3) Готово ✅"
    )


def _format_expires(expires_at: str) -> str:
    try:
        parsed = datetime.fromisoformat(expires_at)
    except ValueError:
        return expires_at
    return parsed.strftime("%Y-%m-%d %H:%M UTC")
