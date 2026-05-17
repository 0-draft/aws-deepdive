from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from datetime import UTC, datetime

import feedparser

from .config import load_sources, track_dir
from .schema import Item

USER_AGENT = "aws-deepdive/0.1 (+https://github.com/0-draft/aws-deepdive)"


def _id(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def _iso(time_struct) -> str:
    if not time_struct:
        return datetime.now(UTC).isoformat()
    return datetime(*time_struct[:6], tzinfo=UTC).isoformat()


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _summary(entry) -> str:
    raw = entry.get("summary") or entry.get("description") or ""
    return _strip_html(raw)[:500]


def _title(entry) -> str:
    return html.unescape((entry.get("title") or "").strip())


def _severity(entry) -> str | None:
    title = (entry.get("title") or "").lower()
    for s in ("critical", "high", "medium", "low"):
        if s in title:
            return s
    return None


def entry_to_item(entry, sid: str, track: str, now: datetime) -> dict | None:
    """Pure conversion from a feedparser entry to an Item dict. Returns None if unusable."""
    link = entry.get("link") or ""
    if not link:
        return None
    return Item(
        id=_id(link),
        track=track,
        source=f"rss:{sid}",
        source_kind="rss",
        url=link,
        title=_title(entry),
        summary=_summary(entry),
        published_at=_iso(entry.get("published_parsed") or entry.get("updated_parsed")),
        fetched_at=now.isoformat(),
        tags=[t.term for t in entry.get("tags", []) if hasattr(t, "term")],
        severity=_severity(entry),
    ).to_dict()


def collect(track: str) -> None:
    sources = load_sources(track)
    feeds = sources.get("rss") or []
    now = datetime.now(UTC)
    items: list[dict] = []
    for feed in feeds:
        sid, url = feed["id"], feed["url"]
        try:
            parsed = feedparser.parse(url, request_headers={"User-Agent": USER_AGENT})
        except Exception as e:
            print(f"[collect_rss] {sid}: error {e}")
            continue
        if getattr(parsed, "bozo", 0) and not parsed.entries:
            print(
                f"[collect_rss] {sid}: feed parse warning ({getattr(parsed, 'bozo_exception', '')})"
            )
        for entry in parsed.entries:
            item = entry_to_item(entry, sid, track, now)
            if item is not None:
                items.append(item)
    out = track_dir(track) / "data" / "raw" / f"rss-{now:%Y-%m-%d}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(items, indent=2, ensure_ascii=False))
    print(f"[collect_rss] {track}: {len(items)} items -> {out.relative_to(track_dir(track))}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", required=True)
    collect(ap.parse_args().track)


if __name__ == "__main__":
    main()
