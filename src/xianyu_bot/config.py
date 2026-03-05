"""Configuration for Xianyu API based auto-delivery bot."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def code_db_path_from_env() -> Path:
    """Return SQLite path used by code pool."""
    return Path(os.getenv("XIANYU_CODE_DB", "data/xianyu_codes.db"))


def _as_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _normalize_path(path: str) -> str:
    path = path.strip()
    if not path:
        return path
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not path.startswith("/"):
        return f"/{path}"
    return path


@dataclass(frozen=True)
class XianyuConfig:
    """Runtime configuration for Xianyu API integration."""

    api_base_url: str
    pending_orders_path: str
    send_message_path: str
    pending_orders_method: str
    send_message_method: str
    cookie: str
    user_agent: str
    request_timeout_seconds: int
    poll_interval_seconds: int
    db_path: Path
    message_template: str
    pending_orders_list_path: str
    order_id_key: str
    buyer_id_key: str
    buyer_name_key: str
    chat_id_key: str
    send_body_template: str
    send_success_path: str
    send_success_value: str

    @classmethod
    def from_env(cls) -> "XianyuConfig":
        """Load config from environment and validate required fields."""
        config = cls(
            api_base_url=os.getenv("XIANYU_API_BASE_URL", "").rstrip("/"),
            pending_orders_path=_normalize_path(os.getenv("XIANYU_PENDING_ORDERS_PATH", "")),
            send_message_path=_normalize_path(os.getenv("XIANYU_SEND_MESSAGE_PATH", "")),
            pending_orders_method=os.getenv("XIANYU_PENDING_ORDERS_METHOD", "GET").upper(),
            send_message_method=os.getenv("XIANYU_SEND_MESSAGE_METHOD", "POST").upper(),
            cookie=os.getenv("XIANYU_COOKIE", "").strip(),
            user_agent=os.getenv(
                "XIANYU_USER_AGENT",
                (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
            ).strip(),
            request_timeout_seconds=_as_int("XIANYU_REQUEST_TIMEOUT_SECONDS", 20),
            poll_interval_seconds=_as_int("XIANYU_POLL_INTERVAL_SECONDS", 15),
            db_path=code_db_path_from_env(),
            message_template=os.getenv(
                "XIANYU_MESSAGE_TEMPLATE",
                "Your redemption code is {code}. Order: {order_id}",
            ),
            pending_orders_list_path=os.getenv("XIANYU_PENDING_ORDERS_LIST_PATH", "data.orders"),
            order_id_key=os.getenv("XIANYU_ORDER_ID_KEY", "order_id"),
            buyer_id_key=os.getenv("XIANYU_BUYER_ID_KEY", "buyer_id"),
            buyer_name_key=os.getenv("XIANYU_BUYER_NAME_KEY", "buyer_name"),
            chat_id_key=os.getenv("XIANYU_CHAT_ID_KEY", "chat_id"),
            send_body_template=os.getenv(
                "XIANYU_SEND_BODY_TEMPLATE",
                (
                    '{"order_id":"{order_id}",'
                    '"chat_id":"{chat_id}",'
                    '"buyer_id":"{buyer_id}",'
                    '"message":"{message}"}'
                ),
            ),
            send_success_path=os.getenv("XIANYU_SEND_SUCCESS_PATH", "success"),
            send_success_value=os.getenv("XIANYU_SEND_SUCCESS_VALUE", "true"),
        )
        config._validate_required()
        return config

    def _validate_required(self) -> None:
        missing: list[str] = []
        if not self.api_base_url:
            missing.append("XIANYU_API_BASE_URL")
        if not self.pending_orders_path:
            missing.append("XIANYU_PENDING_ORDERS_PATH")
        if not self.send_message_path:
            missing.append("XIANYU_SEND_MESSAGE_PATH")
        if not self.cookie:
            missing.append("XIANYU_COOKIE")

        if missing:
            fields = ", ".join(missing)
            raise ValueError(f"Missing required Xianyu config: {fields}")
