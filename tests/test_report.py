from __future__ import annotations

import json
from datetime import timedelta

from awsdd.report import render

from .conftest import NOW


def _scored(items: list[dict]) -> str:
    return json.dumps(items)


def _item(**overrides) -> dict:
    base = {
        "id": "x",
        "track": "iam",
        "source": "rss:src",
        "source_kind": "rss",
        "url": "https://example.com",
        "title": "Item title",
        "summary": "",
        "published_at": NOW.isoformat(),
        "fetched_at": NOW.isoformat(),
        "tags": [],
        "severity": None,
        "score": 5.0,
        "score_breakdown": {},
    }
    base.update(overrides)
    return base


def test_daily_report_contains_recent_items(make_track):
    td = make_track("iam")
    (td / "data" / "scored.json").write_text(_scored([_item()]))

    render("iam", "daily")

    daily_dir = td / "reports" / "daily"
    files = list(daily_dir.glob("*.md"))
    assert len(files) == 1
    body = files[0].read_text()
    assert "Daily update" in body
    assert "Item title" in body
    assert "score 5.00" in body


def test_weekly_report_includes_more_items(make_track):
    td = make_track("iam")
    items = [
        _item(id=str(i), url=f"https://ex.com/{i}", title=f"t{i}", score=float(i))
        for i in range(30)
    ]
    (td / "data" / "scored.json").write_text(_scored(items))

    render("iam", "weekly")

    files = list((td / "reports" / "weekly").glob("*.md"))
    assert len(files) == 1
    body = files[0].read_text()
    assert "Weekly digest" in body
    # daily caps at 10, weekly at 25
    assert body.count("- [") == 25


def test_fallback_to_top_n_when_window_empty(make_track):
    td = make_track("iam")
    old_pub = (NOW - timedelta(days=60)).isoformat()
    (td / "data" / "scored.json").write_text(_scored([_item(published_at=old_pub)]))

    render("iam", "daily")

    body = next((td / "reports" / "daily").glob("*.md")).read_text()
    assert "No items in window" in body
    assert "Item title" in body  # fallback shows the old item anyway


def test_no_scored_file_yields_empty_report(make_track):
    td = make_track("iam")
    render("iam", "daily")
    body = next((td / "reports" / "daily").glob("*.md")).read_text()
    assert "No items at all" in body


def test_gt_in_url_is_escaped(make_track):
    # Regression: a `>` in the URL would close the `[t](<url>)` angle pair
    # early and break Markdown link parsing.
    td = make_track("iam")
    (td / "data" / "scored.json").write_text(_scored([_item(url="https://example.com/?q=a>b")]))
    render("iam", "daily")
    body = next((td / "reports" / "daily").glob("*.md")).read_text()
    assert "%3E" in body
    assert "a>b" not in body
