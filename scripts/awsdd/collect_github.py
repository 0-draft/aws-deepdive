from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import load_sources, track_dir
from .schema import Item

API = "https://api.github.com"
USER_AGENT = "aws-deepdive/0.1 (+https://github.com/0-draft/aws-deepdive)"
FETCH_TIMEOUT = 30
MAX_RESPONSE_BYTES = 10 * 1024 * 1024  # 10 MiB safety cap per page
MAX_PAGES = 5  # follow Link.rel="next" up to this many pages per repo


def _id(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def _headers() -> dict[str, str]:
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": USER_AGENT,
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


_NEXT_LINK_RE = re.compile(r'<([^>]+)>;\s*rel="next"')


def _next_url(link_header: str | None) -> str | None:
    if not link_header:
        return None
    m = _NEXT_LINK_RE.search(link_header)
    return m.group(1) if m else None


def _get_page(url: str) -> tuple[list[dict], str | None]:
    """Fetch one page. Returns (items, next_url). Empty list + None on error."""
    req = Request(url, headers=_headers())
    try:
        with urlopen(req, timeout=FETCH_TIMEOUT) as r:
            # Read one extra byte so we can detect (and refuse) responses that
            # would otherwise be silently truncated mid-multibyte char and yield
            # a corrupt JSONDecodeError downstream.
            raw = r.read(MAX_RESPONSE_BYTES + 1)
            link = r.headers.get("Link")
        if len(raw) > MAX_RESPONSE_BYTES:
            print(
                f"[collect_github] {url}: response exceeded {MAX_RESPONSE_BYTES} bytes; "
                f"skipping (raise per_page or implement narrower paging)"
            )
            return [], None
        # Strict decode so a real encoding bug surfaces instead of being
        # masked by errors='replace' that would also corrupt the JSON.
        res = json.loads(raw.decode("utf-8"))
    except HTTPError as e:
        print(f"[collect_github] {url}: HTTP {e.code}")
        return [], None
    except (URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"[collect_github] {url}: error {e}")
        return [], None
    # GitHub returns a JSON object (not a list) on error envelopes (rate-limit etc.);
    # guard so callers can iterate safely.
    items = res if isinstance(res, list) else []
    return items, _next_url(link)


def _get_all(path: str) -> list[dict]:
    """Follow Link.rel="next" up to MAX_PAGES pages."""
    url = f"{API}{path}"
    out: list[dict] = []
    for _ in range(MAX_PAGES):
        items, nxt = _get_page(url)
        out.extend(items)
        if not nxt:
            break
        url = nxt
    return out


def release_to_item(rel: dict, repo: str, track: str, now: datetime) -> dict | None:
    """Pure conversion from a GitHub Releases API dict to an Item dict. None if draft or missing url."""
    url = rel.get("html_url") or ""
    if not url or rel.get("draft"):
        return None
    return Item(
        id=_id(url),
        track=track,
        source=f"github:{repo}",
        source_kind="github",
        url=url,
        title=(rel.get("name") or rel.get("tag_name") or "").strip(),
        summary=(rel.get("body") or "")[:500],
        # epoch fallback so items missing both timestamps sink rather than rise
        published_at=(
            rel.get("published_at") or rel.get("created_at") or "1970-01-01T00:00:00+00:00"
        ),
        fetched_at=now.isoformat(),
        tags=["prerelease"] if rel.get("prerelease") else [],
    ).to_dict()


def collect(track: str) -> None:
    sources = load_sources(track)
    repos = sources.get("github") or []
    now = datetime.now(UTC)
    items: list[dict] = []
    for entry in repos:
        # defensive: skip malformed config rather than crashing the whole track
        repo = entry.get("repo")
        if not repo:
            print(f"[collect_github] skipping malformed entry: {entry!r}")
            continue
        per_page = entry.get("per_page", 50)
        releases = _get_all(f"/repos/{repo}/releases?per_page={per_page}")
        for rel in releases:
            item = release_to_item(rel, repo, track, now)
            if item is not None:
                items.append(item)
    out = track_dir(track) / "data" / "raw" / f"github-{now:%Y-%m-%d}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[collect_github] {track}: {len(items)} items -> {out.relative_to(track_dir(track))}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", required=True)
    collect(ap.parse_args().track)


if __name__ == "__main__":
    main()
