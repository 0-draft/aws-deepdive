from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta

from ._dates import parse_iso
from .config import track_dir

TOP_N = {"daily": 10, "weekly": 25}
WINDOW = {"daily": timedelta(days=2), "weekly": timedelta(days=7)}


def _filename(mode: str, now: datetime) -> str:
    if mode == "daily":
        return f"{now:%Y-%m-%d}.md"
    iso_year, iso_week, _ = now.isocalendar()
    return f"{iso_year}-W{iso_week:02d}.md"


def render(track: str, mode: str) -> None:
    p = track_dir(track) / "data" / "scored.json"
    items: list[dict] = json.loads(p.read_text()) if p.exists() else []
    now = datetime.now(UTC)
    cutoff = now - WINDOW[mode]
    fresh = [it for it in items if parse_iso(it.get("published_at", "")) >= cutoff]
    fresh.sort(key=lambda x: x.get("score", 0.0), reverse=True)

    used_fallback = False
    if fresh:
        top = fresh[: TOP_N[mode]]
    else:
        # Fall back to top-N by score regardless of window so the report is never empty.
        top = items[: TOP_N[mode]]
        used_fallback = True

    label = "Weekly digest" if mode == "weekly" else "Daily update"
    window_days = WINDOW[mode].total_seconds() / 86400.0

    lines: list[str] = []
    lines.append(f"# {track} — {label} ({now:%Y-%m-%d})")
    lines.append("")
    lines.append(
        f"Window: last {window_days:.0f} day(s) · items in window: **{len(fresh)}** · top shown: **{len(top)}**"
        + (
            "  \n_No items in window — showing top by score across all collected items._"
            if used_fallback
            else ""
        )
    )
    lines.append("")

    if not top:
        lines.append("_No items at all._")
    else:
        groups: dict[str, list[dict]] = {}
        for it in top:
            groups.setdefault(it.get("source_kind", "other"), []).append(it)
        for kind in ("rss", "github", "other"):
            g = groups.get(kind)
            if not g:
                continue
            lines.append(f"## {kind.upper()}")
            lines.append("")
            for it in g:
                # escape both brackets so titles like "[CVE-...] thing" don't
                # collide with markdown link parsing
                title = (it.get("title") or "(untitled)").replace("[", r"\[").replace("]", r"\]")
                url = it.get("url", "")
                src = it.get("source", "")
                pub = (it.get("published_at") or "")[:10]
                score = float(it.get("score", 0.0))
                # angle-bracket the URL: AWS links sometimes contain `(` / `)`,
                # which break vanilla Markdown link parsing.
                lines.append(f"- [{title}](<{url}>) — `{src}` · {pub} · **score {score:.2f}**")
            lines.append("")

    out = track_dir(track) / "reports" / mode / _filename(mode, now)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines))
    print(f"[report] {track}/{mode}: {out.relative_to(track_dir(track))}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", required=True)
    ap.add_argument("--mode", choices=["daily", "weekly"], required=True)
    args = ap.parse_args()
    render(args.track, args.mode)


if __name__ == "__main__":
    main()
