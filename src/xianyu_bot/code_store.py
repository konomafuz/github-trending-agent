"""SQLite-backed code pool for auto-delivery."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ImportResult:
    inserted: int
    duplicates: int


class CodeStore:
    """Manages code inventory and delivery records."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def import_codes(self, codes: Iterable[str], source: str = "manual") -> ImportResult:
        """Insert new codes into pool and ignore duplicates."""
        cleaned = [c.strip() for c in codes if c.strip()]
        if not cleaned:
            return ImportResult(inserted=0, duplicates=0)

        inserted = 0
        now = _now_iso()
        with self._connect() as conn:
            for code in cleaned:
                result = conn.execute(
                    """
                    INSERT OR IGNORE INTO codes(code, status, source, created_at)
                    VALUES(?, 'AVAILABLE', ?, ?)
                    """,
                    (code, source, now),
                )
                inserted += result.rowcount
        return ImportResult(inserted=inserted, duplicates=len(cleaned) - inserted)

    def reserve_code(self, order_id: str) -> str | None:
        """Reserve one available code atomically for an order."""
        now = _now_iso()
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT code FROM codes WHERE status='AVAILABLE' ORDER BY rowid LIMIT 1"
            ).fetchone()
            if row is None:
                conn.commit()
                return None

            code = str(row[0])
            updated = conn.execute(
                """
                UPDATE codes
                SET status='RESERVED', reserved_order_id=?, reserved_at=?
                WHERE code=? AND status='AVAILABLE'
                """,
                (order_id, now, code),
            ).rowcount
            if updated != 1:
                conn.rollback()
                return None
            conn.commit()
            return code

    def release_code(self, code: str, order_id: str) -> None:
        """Return reserved code to pool when send fails."""
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE codes
                SET status='AVAILABLE', reserved_order_id=NULL, reserved_at=NULL
                WHERE code=? AND status='RESERVED' AND reserved_order_id=?
                """,
                (code, order_id),
            )

    def mark_sent(self, order_id: str, code: str, buyer_id: str | None) -> None:
        """Mark code as sent and persist delivery record."""
        now = _now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO deliveries(order_id, code, buyer_id, status, error, created_at, updated_at)
                VALUES(?, ?, ?, 'SENT', NULL, ?, ?)
                ON CONFLICT(order_id) DO UPDATE SET
                    code=excluded.code,
                    buyer_id=excluded.buyer_id,
                    status='SENT',
                    error=NULL,
                    updated_at=excluded.updated_at
                """,
                (order_id, code, buyer_id, now, now),
            )
            conn.execute(
                """
                UPDATE codes
                SET status='SENT', sent_order_id=?, sent_at=?
                WHERE code=?
                """,
                (order_id, now, code),
            )

    def mark_failed(self, order_id: str, buyer_id: str | None, error: str) -> None:
        """Record failed attempt for observability."""
        now = _now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO deliveries(order_id, code, buyer_id, status, error, created_at, updated_at)
                VALUES(?, NULL, ?, 'FAILED', ?, ?, ?)
                ON CONFLICT(order_id) DO UPDATE SET
                    status='FAILED',
                    error=excluded.error,
                    updated_at=excluded.updated_at
                """,
                (order_id, buyer_id, error[:1024], now, now),
            )

    def mark_no_code(self, order_id: str, buyer_id: str | None) -> None:
        """Record that no code is available now."""
        now = _now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO deliveries(order_id, code, buyer_id, status, error, created_at, updated_at)
                VALUES(?, NULL, ?, 'NO_CODE', 'No code available', ?, ?)
                ON CONFLICT(order_id) DO UPDATE SET
                    status='NO_CODE',
                    error='No code available',
                    updated_at=excluded.updated_at
                """,
                (order_id, buyer_id, now, now),
            )

    def is_sent(self, order_id: str) -> bool:
        """Return true when this order already has successful delivery."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM deliveries WHERE order_id=? AND status='SENT' LIMIT 1",
                (order_id,),
            ).fetchone()
        return row is not None

    def inventory(self) -> dict[str, int]:
        """Return code count by status."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) FROM codes GROUP BY status"
            ).fetchall()
        return {str(status): int(count) for status, count in rows}

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS codes (
                    code TEXT PRIMARY KEY,
                    status TEXT NOT NULL CHECK(status IN ('AVAILABLE', 'RESERVED', 'SENT')),
                    source TEXT,
                    reserved_order_id TEXT,
                    sent_order_id TEXT,
                    reserved_at TEXT,
                    sent_at TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_codes_status ON codes(status);

                CREATE TABLE IF NOT EXISTS deliveries (
                    order_id TEXT PRIMARY KEY,
                    code TEXT,
                    buyer_id TEXT,
                    status TEXT NOT NULL CHECK(status IN ('SENT', 'FAILED', 'NO_CODE')),
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_deliveries_status ON deliveries(status);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn
