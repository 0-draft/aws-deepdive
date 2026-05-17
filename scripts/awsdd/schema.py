from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Item:
    id: str
    track: str
    source: str          # e.g. "rss:aws-security-blog"
    source_kind: str     # "rss" | "github"
    url: str
    title: str
    summary: str
    published_at: str    # ISO8601 UTC
    fetched_at: str      # ISO8601 UTC
    tags: list[str] = field(default_factory=list)
    severity: str | None = None
    score: float = 0.0
    score_breakdown: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
