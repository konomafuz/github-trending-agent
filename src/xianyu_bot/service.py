"""Business orchestration for Xianyu auto-delivery."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from .client import PendingOrder, XianyuApiClient
from .code_store import CodeStore
from .config import XianyuConfig

logger = logging.getLogger(__name__)


class _SafeFormatDict(dict[str, str]):
    def __missing__(self, key: str) -> str:
        return ""


@dataclass(frozen=True)
class DeliveryStats:
    scanned: int = 0
    sent: int = 0
    skipped_sent: int = 0
    failed: int = 0
    no_code: int = 0


class XianyuDeliveryService:
    """Coordinates pending-order polling, code reservation and send."""

    def __init__(
        self,
        config: XianyuConfig,
        client: XianyuApiClient,
        store: CodeStore,
    ) -> None:
        self.config = config
        self.client = client
        self.store = store

    def run_once(self) -> DeliveryStats:
        """Process pending orders one time."""
        orders = self.client.fetch_pending_orders()
        scanned = len(orders)
        sent = 0
        skipped_sent = 0
        failed = 0
        no_code = 0

        for order in orders:
            if self.store.is_sent(order.order_id):
                skipped_sent += 1
                continue

            code = self.store.reserve_code(order.order_id)
            if code is None:
                no_code += 1
                self.store.mark_no_code(order.order_id, order.buyer_id)
                logger.warning("No available code for order=%s", order.order_id)
                continue

            message = self._build_message(order, code)
            try:
                self.client.send_message(order, message)
            except Exception as exc:  # noqa: BLE001 - keep daemon resilient
                failed += 1
                self.store.release_code(code, order.order_id)
                self.store.mark_failed(order.order_id, order.buyer_id, str(exc))
                logger.exception("Send failed for order=%s: %s", order.order_id, exc)
                continue

            sent += 1
            self.store.mark_sent(order.order_id, code, order.buyer_id)
            logger.info("Sent code for order=%s code=%s", order.order_id, code)

        return DeliveryStats(
            scanned=scanned,
            sent=sent,
            skipped_sent=skipped_sent,
            failed=failed,
            no_code=no_code,
        )

    def run_forever(self) -> None:
        """Keep polling with fixed interval."""
        logger.info(
            "Xianyu bot started. interval=%ss db=%s",
            self.config.poll_interval_seconds,
            self.config.db_path,
        )
        while True:
            try:
                stats = self.run_once()
                logger.info(
                    (
                        "Cycle complete scanned=%d sent=%d skipped=%d failed=%d no_code=%d"
                    ),
                    stats.scanned,
                    stats.sent,
                    stats.skipped_sent,
                    stats.failed,
                    stats.no_code,
                )
            except Exception as exc:  # noqa: BLE001 - keep daemon resilient
                logger.exception("Cycle crashed: %s", exc)

            time.sleep(self.config.poll_interval_seconds)

    def _build_message(self, order: PendingOrder, code: str) -> str:
        values = _SafeFormatDict(
            {
                "code": code,
                "order_id": order.order_id,
                "buyer_id": order.buyer_id or "",
                "buyer_name": order.buyer_name or "",
                "chat_id": order.chat_id or "",
            }
        )
        return self.config.message_template.format_map(values)
