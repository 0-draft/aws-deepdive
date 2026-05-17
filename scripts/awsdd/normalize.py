from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta

from ._dates import parse_iso
from .config import track_dir

# Retention: drop items older than this from normalized.json so the file
# (which is committed and loaded entirely at build time) doesn't grow
# unbounded as the project ages. 180 days keeps roughly a release cycle of
# context while bounding repo size.
RETENTION = timedelta(days=180)


def normalize(track: str, retention: timedelta = RETENTION) -> None:
    raw_dir = track_dir(track) / "data" / "raw"
    out = track_dir(track) / "data" / "normalized.json"

    by_id: dict[str, dict] = {}
    if out.exists():
        try:
            for it in json.loads(out.read_text()):
                by_id[it["id"]] = it
        except (OSError, json.JSONDecodeError) as e:
            print(f"[normalize] existing normalized.json unreadable: {e}")

    if raw_dir.exists():
        for path in sorted(raw_dir.glob("*.json")):
            try:
                for it in json.loads(path.read_text()):
                    prev = by_id.get(it["id"])
                    if prev:
                        # keep earliest fetched_at as a proxy for "first seen"
                        it["fetched_at"] = min(
                            prev.get("fetched_at", it["fetched_at"]), it["fetched_at"]
                        )
                    by_id[it["id"]] = it
            except (OSError, json.JSONDecodeError) as e:
                print(f"[normalize] {path.name}: {e}")

    cutoff = datetime.now(UTC) - retention
    before = len(by_id)
    kept = {k: v for k, v in by_id.items() if parse_iso(v.get("published_at", "")) >= cutoff}
    pruned = before - len(kept)

    items = sorted(kept.values(), key=lambda x: x.get("published_at", ""), reverse=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(items, indent=2, ensure_ascii=False))
    suffix = f" (pruned {pruned} older than {retention.days}d)" if pruned else ""
    print(f"[normalize] {track}: {len(items)} unique items{suffix}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", required=True)
    normalize(ap.parse_args().track)


if __name__ == "__main__":
    main()
