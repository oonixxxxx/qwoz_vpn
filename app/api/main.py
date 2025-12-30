from __future__ import annotations

import base64
import os
import uuid
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Optional

import qrcode
from fastapi import FastAPI, HTTPException

from app.api.db import UserRepository, create_user_record, get_connection, init_db
from app.api.schemas import ConfigResponse, ProvisionRequest, RevokeResponse, UserResponse
from app.api.xray import add_client, remove_client

XRAY_HOST = os.getenv("XRAY_PUBLIC_HOST", "vpn.example.com")
XRAY_PORT = int(os.getenv("XRAY_PUBLIC_PORT", "443"))
XRAY_TAG = os.getenv("XRAY_PROFILE_TAG", "NixVPN")

app = FastAPI(title="Xray Provisioning API", version="1.0.0")


@app.on_event("startup")
async def startup() -> None:
    init_db()


def build_vless_url(client_uuid: str, email: str) -> str:
    return (
        f"vless://{client_uuid}@{XRAY_HOST}:{XRAY_PORT}"
        f"?encryption=none&security=tls&type=tcp#{XRAY_TAG}-{email}"
    )


def generate_qr_base64(payload: str) -> str:
    qr = qrcode.QRCode(border=2, box_size=6)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


@app.post("/users/{telegram_id}/provision", response_model=UserResponse)
async def provision_user(telegram_id: int, payload: ProvisionRequest) -> UserResponse:
    expires_at = datetime.now(timezone.utc) + timedelta(days=payload.plan_days)
    client_uuid = str(uuid.uuid4())
    email = f"tg_{telegram_id}"
    key = f"{telegram_id}-{client_uuid[:8]}"

    record = create_user_record(
        telegram_id=telegram_id,
        uuid=client_uuid,
        email=email,
        key=key,
        expires_at=expires_at,
        status="active",
    )

    with get_connection() as connection:
        repo = UserRepository(connection)
        repo.ensure_schema()
        repo.upsert(record)

    add_client(client_uuid, email)

    return UserResponse(
        telegram_id=telegram_id,
        uuid=client_uuid,
        key=key,
        status="active",
        created_at=record.created_at,
        expires_at=record.expires_at,
        vless_url=build_vless_url(client_uuid, email),
    )


@app.post("/users/{telegram_id}/revoke", response_model=RevokeResponse)
async def revoke_user(telegram_id: int) -> RevokeResponse:
    with get_connection() as connection:
        repo = UserRepository(connection)
        record = repo.get(telegram_id)
        if not record:
            raise HTTPException(status_code=404, detail="User not found")

        revoked_at = datetime.now(timezone.utc).isoformat()
        repo.update_status(telegram_id, "revoked", revoked_at)

    remove_client(record.uuid)

    return RevokeResponse(
        telegram_id=telegram_id,
        status="revoked",
        revoked_at=revoked_at,
    )


@app.get("/users/{telegram_id}", response_model=UserResponse)
async def get_user(telegram_id: int) -> UserResponse:
    with get_connection() as connection:
        repo = UserRepository(connection)
        record = repo.get(telegram_id)
        if not record:
            raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        telegram_id=record.telegram_id,
        uuid=record.uuid,
        key=record.key,
        status=record.status,
        created_at=record.created_at,
        expires_at=record.expires_at,
        vless_url=build_vless_url(record.uuid, record.email),
    )


@app.get("/users/{telegram_id}/config", response_model=ConfigResponse)
async def get_user_config(telegram_id: int) -> ConfigResponse:
    with get_connection() as connection:
        repo = UserRepository(connection)
        record = repo.get(telegram_id)
        if not record:
            raise HTTPException(status_code=404, detail="User not found")

    vless_url = build_vless_url(record.uuid, record.email)
    qr_base64 = generate_qr_base64(vless_url)

    return ConfigResponse(
        telegram_id=record.telegram_id,
        vless_url=vless_url,
        qr_base64=qr_base64,
        expires_at=record.expires_at,
    )
