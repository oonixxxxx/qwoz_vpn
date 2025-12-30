from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_XRAY_CONFIG = BASE_DIR / "xray" / "config.json"


def get_config_path() -> Path:
    env_path = os.getenv("XRAY_CONFIG_PATH")
    return Path(env_path) if env_path else DEFAULT_XRAY_CONFIG


def load_config() -> Dict[str, Any]:
    config_path = get_config_path()
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(default_config(), indent=2), encoding="utf-8")
    return json.loads(config_path.read_text(encoding="utf-8"))


def save_config(config: Dict[str, Any]) -> None:
    config_path = get_config_path()
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def default_config() -> Dict[str, Any]:
    return {
        "log": {
            "loglevel": "warning",
        },
        "inbounds": [
            {
                "tag": "vless-in",
                "port": int(os.getenv("XRAY_INBOUND_PORT", "443")),
                "listen": "0.0.0.0",
                "protocol": "vless",
                "settings": {
                    "clients": [],
                    "decryption": "none",
                },
                "streamSettings": {
                    "network": "tcp",
                    "security": "tls",
                },
            }
        ],
        "outbounds": [
            {
                "tag": "direct",
                "protocol": "freedom",
                "settings": {},
            }
        ],
    }


def _get_vless_clients(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    for inbound in config.get("inbounds", []):
        if inbound.get("protocol") == "vless":
            settings = inbound.setdefault("settings", {})
            return settings.setdefault("clients", [])
    raise ValueError("VLESS inbound not found in Xray config")


def add_client(uuid: str, email: str) -> None:
    config = load_config()
    clients = _get_vless_clients(config)
    if not any(client.get("id") == uuid for client in clients):
        clients.append({"id": uuid, "email": email})
    save_config(config)


def remove_client(uuid: str) -> None:
    config = load_config()
    clients = _get_vless_clients(config)
    updated_clients = [client for client in clients if client.get("id") != uuid]
    for inbound in config.get("inbounds", []):
        if inbound.get("protocol") == "vless":
            inbound.setdefault("settings", {})["clients"] = updated_clients
    save_config(config)
