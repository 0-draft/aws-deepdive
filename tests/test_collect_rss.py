from __future__ import annotations

import feedparser
from awsdd.collect_rss import _summary, _title, entry_to_item

from .conftest import FIXTURES, NOW


def _parsed():
    return feedparser.parse((FIXTURES / "rss_sample.xml").read_text())


def test_entry_to_item_basic():
    entries = _parsed().entries
    item = entry_to_item(entries[0], "test-src", "iam", NOW)
    assert item is not None
    assert item["track"] == "iam"
    assert item["source"] == "rss:test-src"
    assert item["source_kind"] == "rss"
    assert "roles-anywhere" in item["title"].lower() or "Roles Anywhere" in item["title"]
    assert item["url"].startswith("https://")
    assert item["id"]  # 16-hex sha
    assert len(item["id"]) == 16


def test_html_in_summary_is_stripped_and_unescaped():
    entries = _parsed().entries
    item = entry_to_item(entries[0], "src", "iam", NOW)
    assert "<p>" not in item["summary"]
    assert "&lt;" not in item["summary"]
    assert "X.509" in item["summary"]


def test_severity_detected_from_title():
    entries = _parsed().entries
    item = entry_to_item(entries[2], "src", "security", NOW)
    assert item["severity"] == "critical"


def test_entry_without_link_returns_none():
    fake = type("E", (), {"get": lambda self, k, d=None: "" if k == "link" else d})()
    assert entry_to_item(fake, "src", "iam", NOW) is None


def test_title_helper_unescapes():
    fake = type("E", (), {"get": lambda self, k, d=None: "A &amp; B" if k == "title" else d})()
    assert _title(fake) == "A & B"


def test_summary_helper_strips_html():
    fake = type(
        "E", (), {"get": lambda self, k, d=None: "<b>hi</b> there" if k == "summary" else d}
    )()
    assert _summary(fake) == "hi there"
