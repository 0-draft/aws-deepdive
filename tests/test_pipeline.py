"""End-to-end smoke: normalize → score → report against fixture data, no network."""

from __future__ import annotations

import json

from awsdd.normalize import normalize
from awsdd.report import render
from awsdd.score import score

from .conftest import NOW

SOURCES_YAML = """
keywords:
  primary: [roles-anywhere, trust-anchor]
  secondary: [iam]
source_weights:
  default: 1.0
  rss:test: 2.0
rss: []
github: []
"""


def _raw_item(id_: str, title: str, **overrides) -> dict:
    base = {
        "id": id_,
        "track": "smoke",
        "source": "rss:test",
        "source_kind": "rss",
        "url": f"https://example.com/{id_}",
        "title": title,
        "summary": "",
        "published_at": NOW.isoformat(),
        "fetched_at": NOW.isoformat(),
        "tags": [],
        "severity": None,
    }
    base.update(overrides)
    return base


def test_normalize_score_report_pipeline(make_track):
    td = make_track("smoke", sources_yaml=SOURCES_YAML)
    raw = td / "data" / "raw"
    (raw / "rss-2026-05-17.json").write_text(
        json.dumps(
            [
                _raw_item("a", "IAM Roles Anywhere trust-anchor improvements"),
                _raw_item("b", "Generic launch with no keywords"),
            ]
        )
    )

    normalize("smoke")
    score("smoke")
    render("smoke", "daily")
    render("smoke", "weekly")

    scored = json.loads((td / "data" / "scored.json").read_text())
    # the IAM item must outrank the generic one
    assert scored[0]["id"] == "a"
    assert scored[0]["score"] > scored[1]["score"]

    daily = next((td / "reports" / "daily").glob("*.md")).read_text()
    weekly = next((td / "reports" / "weekly").glob("*.md")).read_text()
    assert "IAM Roles Anywhere" in daily
    assert "IAM Roles Anywhere" in weekly
