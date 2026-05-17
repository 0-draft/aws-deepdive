from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .config import load_sources, track_dir
from .schema import Item

API = "https://api.github.com"
USER_AGENT = "aws-deepdive/0.1 (+https://github.com/0-draft/aws-deepdive)"


def _id(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def _get(path: str) -> list[dict]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": USER_AGENT,
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(f"{API}{path}", headers=headers)
    try:
        with urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except HTTPError as e:
        print(f"[collect_github] {path}: HTTP {e.code}")
        return []
    except Exception as e:
        print(f"[collect_github] {path}: error {e}")
        return []


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
        published_at=(rel.get("published_at") or rel.get("created_at") or now.isoformat()),
        fetched_at=now.isoformat(),
        tags=["prerelease"] if rel.get("prerelease") else [],
    ).to_dict()


def collect(track: str) -> None:
    sources = load_sources(track)
    repos = sources.get("github") or []
    now = datetime.now(UTC)
    items: list[dict] = []
    for entry in repos:
        repo = entry["repo"]
        per_page = entry.get("per_page", 20)
        releases = _get(f"/repos/{repo}/releases?per_page={per_page}")
        for rel in releases:
            item = release_to_item(rel, repo, track, now)
            if item is not None:
                items.append(item)
    out = track_dir(track) / "data" / "raw" / f"github-{now:%Y-%m-%d}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(items, indent=2, ensure_ascii=False))
    print(f"[collect_github] {track}: {len(items)} items -> {out.relative_to(track_dir(track))}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", required=True)
    collect(ap.parse_args().track)


if __name__ == "__main__":
    main()
