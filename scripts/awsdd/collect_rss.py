from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.error import URLError
from urllib.request import Request, urlopen

import feedparser

from .config import load_sources, track_dir
from .schema import Item

USER_AGENT = "aws-deepdive/0.1 (+https://github.com/0-draft/aws-deepdive)"
FETCH_TIMEOUT = 30  # seconds
MAX_FEED_BYTES = 10 * 1024 * 1024  # 10 MiB cap to bound memory on hostile / runaway feeds
EPOCH_ISO = "1970-01-01T00:00:00+00:00"


def _id(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def _iso(time_struct) -> str:
    # Fall back to the Unix epoch (not "now") so items with missing dates
    # rank as stale and are not promoted by the freshness signal.
    if not time_struct:
        return EPOCH_ISO
    return datetime(*time_struct[:6], tzinfo=UTC).isoformat()


def _fetch(url: str, timeout: int = FETCH_TIMEOUT) -> str | None:
    """Fetch a feed body with an explicit timeout; None on network failure."""
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=timeout) as r:
            return r.read(MAX_FEED_BYTES).decode("utf-8", errors="replace")
    except (URLError, TimeoutError) as e:
        print(f"[collect_rss] fetch {url}: {e}")
        return None


class _TextExtractor(HTMLParser):
    """Pull text content out of HTML, dropping <script>/<style> bodies entirely.

    Uses stdlib html.parser so it correctly handles entities and `<` / `>`
    inside text content (e.g. "1 < 2 and 4 > 3"), which a regex strip would
    chomp.
    """

    _DROP_CONTENT = frozenset({"script", "style"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._drop_depth = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in self._DROP_CONTENT:
            self._drop_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self._DROP_CONTENT and self._drop_depth > 0:
            self._drop_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._drop_depth == 0:
            self.parts.append(data)


def _strip_html(text: str) -> str:
    # Unescape FIRST so entity-encoded tags like `&lt;script&gt;` become
    # real tags the parser can recognise (otherwise they'd survive as text).
    text = html.unescape(text)
    parser = _TextExtractor()
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        # html.parser is fairly tolerant; if it bails on truly malformed input,
        # fall back to the raw text rather than dropping the whole summary.
        return re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+", " ", "".join(parser.parts)).strip()


def _summary(entry) -> str:
    raw = entry.get("summary") or entry.get("description") or ""
    return _strip_html(raw)[:500]


def _title(entry) -> str:
    return html.unescape((entry.get("title") or "").strip())


_SEVERITY_RE = re.compile(r"\b(critical|high|medium|low)\b", re.IGNORECASE)


def _severity(entry) -> str | None:
    # Word-boundary match: avoids "Slow performance" hitting "low" and
    # "Highlighted" hitting "high".
    title = entry.get("title") or ""
    m = _SEVERITY_RE.search(title)
    return m.group(1).lower() if m else None


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
        # Fetch with an explicit timeout — feedparser.parse(url) has no built-in
        # timeout and a stuck origin would hang the whole pipeline.
        body = _fetch(url)
        if body is None:
            continue
        parsed = feedparser.parse(body)
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
