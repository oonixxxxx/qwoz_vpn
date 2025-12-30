from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProvisionRequest(BaseModel):
    plan_days: int = Field(default=30, ge=1)


class UserResponse(BaseModel):
    telegram_id: int
    uuid: str
    key: str
    status: str
    created_at: str
    expires_at: Optional[str]
    vless_url: Optional[str] = None


class RevokeResponse(BaseModel):
    telegram_id: int
    status: str
    revoked_at: str


class ConfigResponse(BaseModel):
    telegram_id: int
    vless_url: str
    qr_base64: str
    expires_at: Optional[str]
