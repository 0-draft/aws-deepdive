from __future__ import annotations

from datetime import UTC, datetime

EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def parse_iso(s: str) -> datetime:
    """Parse an ISO-8601 string into a UTC-aware datetime.

    Falls back to the Unix epoch (not "now") so corrupted or missing
    timestamps sink to the bottom of freshness rankings instead of being
    promoted to the top.
    """
    try:
        return datetime.fromisoformat(s or "")
    except (ValueError, TypeError):
        return EPOCH
