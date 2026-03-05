"""HTTP client for Xianyu API workflows."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from string import Formatter
from typing import Any
from urllib.parse import urljoin

import requests

from .config import XianyuConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PendingOrder:
    """Represents one pending order candidate for auto-delivery."""

    order_id: str
    buyer_id: str | None = None
    buyer_name: str | None = None
    chat_id: str | None = None


def _extract_path(payload: Any, dotted_path: str) -> Any:
    """Extract nested field using dot path (supports list index tokens)."""
    if dotted_path.strip() in {"", "."}:
        return payload

    current = payload
    for token in dotted_path.split("."):
        token = token.strip()
        if token == "":
            continue

        if isinstance(current, dict):
            current = current.get(token)
            continue

        if isinstance(current, list):
            if not token.isdigit():
                return None
            idx = int(token)
            if idx < 0 or idx >= len(current):
                return None
            current = current[idx]
            continue

        return None

    return current


class _SafeFormatDict(dict[str, str]):
    """Default missing template variables to empty string."""

    def __missing__(self, key: str) -> str:
        return ""


def _render_template(template: str, values: dict[str, str]) -> str:
    """Render string templates safely with strict brace handling."""
    # Validate placeholder syntax before formatting.
    for _, field_name, _, _ in Formatter().parse(template):
        if field_name is None:
            continue
        if field_name == "":
            raise ValueError("Empty placeholder detected in template")
    return template.format_map(_SafeFormatDict(values))


class XianyuApiClient:
    """Wraps the two API calls needed for auto-delivery."""

    def __init__(self, config: XianyuConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json;charset=UTF-8",
                "User-Agent": self.config.user_agent,
                "Cookie": self.config.cookie,
            }
        )

    def fetch_pending_orders(self) -> list[PendingOrder]:
        """Fetch candidate orders from configured endpoint."""
        payload = self._request_json(
            method=self.config.pending_orders_method,
            path=self.config.pending_orders_path,
        )
        raw_orders = _extract_path(payload, self.config.pending_orders_list_path)
        if raw_orders is None:
            logger.warning(
                "Pending orders path %s not found in response",
                self.config.pending_orders_list_path,
            )
            return []
        if not isinstance(raw_orders, list):
            raise ValueError("Pending orders list path does not resolve to a list")

        orders: list[PendingOrder] = []
        for item in raw_orders:
            if not isinstance(item, dict):
                continue

            order_id = str(item.get(self.config.order_id_key, "")).strip()
            if not order_id:
                continue

            orders.append(
                PendingOrder(
                    order_id=order_id,
                    buyer_id=_optional_str(item.get(self.config.buyer_id_key)),
                    buyer_name=_optional_str(item.get(self.config.buyer_name_key)),
                    chat_id=_optional_str(item.get(self.config.chat_id_key)),
                )
            )
        return orders

    def send_message(self, order: PendingOrder, message: str) -> dict[str, Any]:
        """Send one message to buyer for a specific order."""
        values = {
            "order_id": order.order_id,
            "buyer_id": order.buyer_id or "",
            "buyer_name": order.buyer_name or "",
            "chat_id": order.chat_id or "",
            "message": message,
        }
        body_text = _render_template(self.config.send_body_template, values)
        try:
            body = json.loads(body_text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "XIANYU_SEND_BODY_TEMPLATE is not valid JSON after formatting"
            ) from exc

        payload = self._request_json(
            method=self.config.send_message_method,
            path=self.config.send_message_path,
            json_body=body,
        )
        self._assert_send_success(payload)
        return payload

    def _assert_send_success(self, payload: dict[str, Any]) -> None:
        path = self.config.send_success_path.strip()
        if path == "":
            return
        actual = _extract_path(payload, path)
        expected = self.config.send_success_value.strip()
        if expected == "":
            return
        if str(actual).lower() != expected.lower():
            raise RuntimeError(
                f"Send message response not successful: expected {expected}, got {actual}"
            )

    def _request_json(
        self,
        method: str,
        path: str,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = self._build_url(path)
        response = self.session.request(
            method=method,
            url=url,
            json=json_body,
            timeout=self.config.request_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("API response is not a JSON object")
        return data

    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        base = f"{self.config.api_base_url}/"
        return urljoin(base, path.lstrip("/"))


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None
