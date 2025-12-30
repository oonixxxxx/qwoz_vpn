from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "xray.db"


def get_db_path() -> Path:
    env_path = os.getenv("XRAY_DB_PATH")
    return Path(env_path) if env_path else DEFAULT_DB_PATH


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


@dataclass
class UserRecord:
    telegram_id: int
    uuid: str
    email: str
    key: str
    status: str
    created_at: str
    expires_at: Optional[str]


CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    uuid TEXT NOT NULL,
    email TEXT NOT NULL,
    key TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT
);
"""


class UserRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def ensure_schema(self) -> None:
        self.connection.execute(CREATE_USERS_TABLE)
        self.connection.commit()

    def upsert(self, record: UserRecord) -> None:
        self.connection.execute(
            """
            INSERT INTO users (telegram_id, uuid, email, key, status, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                uuid = excluded.uuid,
                email = excluded.email,
                key = excluded.key,
                status = excluded.status,
                created_at = excluded.created_at,
                expires_at = excluded.expires_at
            """,
            (
                record.telegram_id,
                record.uuid,
                record.email,
                record.key,
                record.status,
                record.created_at,
                record.expires_at,
            ),
        )
        self.connection.commit()

    def get(self, telegram_id: int) -> Optional[UserRecord]:
        cursor = self.connection.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )
        row = cursor.fetchone()
        return UserRecord(**row) if row else None

    def list_all(self) -> Iterable[UserRecord]:
        cursor = self.connection.execute("SELECT * FROM users")
        for row in cursor.fetchall():
            yield UserRecord(**row)

    def update_status(self, telegram_id: int, status: str, expires_at: Optional[str]) -> None:
        self.connection.execute(
            "UPDATE users SET status = ?, expires_at = ? WHERE telegram_id = ?",
            (status, expires_at, telegram_id),
        )
        self.connection.commit()



def create_user_record(
    telegram_id: int,
    uuid: str,
    email: str,
    key: str,
    expires_at: Optional[datetime],
    status: str = "active",
) -> UserRecord:
    created_at = datetime.utcnow().isoformat()
    return UserRecord(
        telegram_id=telegram_id,
        uuid=uuid,
        email=email,
        key=key,
        status=status,
        created_at=created_at,
        expires_at=expires_at.isoformat() if expires_at else None,
    )


def init_db() -> None:
    with get_connection() as connection:
        UserRepository(connection).ensure_schema()
