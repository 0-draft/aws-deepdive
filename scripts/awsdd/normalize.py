from __future__ import annotations

import argparse
import json

from .config import track_dir


def normalize(track: str) -> None:
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

    items = sorted(by_id.values(), key=lambda x: x.get("published_at", ""), reverse=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(items, indent=2, ensure_ascii=False))
    print(f"[normalize] {track}: {len(items)} unique items")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", required=True)
    normalize(ap.parse_args().track)


if __name__ == "__main__":
    main()
