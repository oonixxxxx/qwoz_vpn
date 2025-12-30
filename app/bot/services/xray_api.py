from __future__ import annotations

import os
from typing import Optional

import httpx

XRAY_API_URL = os.getenv("XRAY_API_URL", "http://localhost:8000")


class XrayAPIClient:
    def __init__(self, base_url: str = XRAY_API_URL) -> None:
        self.base_url = base_url.rstrip("/")

    async def provision_user(self, telegram_id: int, plan_days: int = 30) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/users/{telegram_id}/provision",
                json={"plan_days": plan_days},
                timeout=15,
            )
            response.raise_for_status()
            return response.json()

    async def revoke_user(self, telegram_id: int) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/users/{telegram_id}/revoke",
                timeout=15,
            )
            response.raise_for_status()
            return response.json()

    async def get_user(self, telegram_id: int) -> Optional[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users/{telegram_id}",
                timeout=15,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    async def get_user_config(self, telegram_id: int) -> Optional[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users/{telegram_id}/config",
                timeout=15,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
