from __future__ import annotations

import argparse
import json
import math
import re
from datetime import UTC, datetime

from ._dates import parse_iso
from .config import load_sources, track_dir

SEVERITY_WEIGHT = {"critical": 3.0, "high": 2.0, "medium": 1.0, "low": 0.5}


def _keyword_hits(keywords: list[str], text: str) -> int:
    """Count word-bounded matches. Substring matching would let `iam` hit
    `diagram` or `sts` hit `tests`, which dilutes the topic signal."""
    return sum(1 for k in keywords if re.search(rf"\b{re.escape(k)}\b", text))


def score_item(item: dict, sources: dict, now: datetime) -> dict[str, float]:
    pub = parse_iso(item.get("published_at", ""))
    days = max(0.0, (now - pub).total_seconds() / 86400.0)
    freshness = math.exp(-days / 14.0)  # ~14-day decay

    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    kws = sources.get("keywords") or {}
    primary = [k.lower() for k in (kws.get("primary") or [])]
    secondary = [k.lower() for k in (kws.get("secondary") or [])]
    p_hits = _keyword_hits(primary, text)
    s_hits = _keyword_hits(secondary, text)
    keyword = p_hits * 2.0 + s_hits * 0.5

    weights = sources.get("source_weights") or {}
    raw_weight = weights.get(item.get("source", ""), weights.get("default", 1.0))
    try:
        source_w = float(raw_weight)
    except (TypeError, ValueError):
        # A config typo (e.g. `rss:foo: bar`) used to abort the whole pipeline.
        # Treat the malformed weight as default = 1.0 and keep scoring.
        source_w = 1.0

    sev_label = (item.get("severity") or "").lower()
    sev = SEVERITY_WEIGHT.get(sev_label, 0.0)

    # Multiplicative: items with zero keyword match only get the freshness baseline,
    # which keeps generic What's-New noise out of topic-specific tracks while still
    # promoting items that match keywords on a high-trust source.
    keyword_signal = keyword * source_w
    total = freshness * 2.0 + keyword_signal + sev
    return {
        "freshness": round(freshness * 2.0, 3),
        "keyword": round(keyword, 3),
        "source": round(source_w, 3),
        "keyword_signal": round(keyword_signal, 3),
        "severity": round(sev, 3),
        "total": round(total, 3),
    }


def score(track: str) -> None:
    p = track_dir(track) / "data" / "normalized.json"
    items: list[dict] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
    sources = load_sources(track)
    now = datetime.now(UTC)
    for it in items:
        b = score_item(it, sources, now)
        it["score"] = b["total"]
        it["score_breakdown"] = b
    items.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    out = track_dir(track) / "data" / "scored.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[score] {track}: scored {len(items)} items")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", required=True)
    score(ap.parse_args().track)


if __name__ == "__main__":
    main()
