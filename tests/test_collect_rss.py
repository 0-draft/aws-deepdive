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


def test_summary_strips_entity_encoded_tags():
    # Regression: some feeds double-encode tags as `&lt;script&gt;...`.
    # The old strip-then-unescape order let those leak through as raw HTML.
    payload = "&lt;script&gt;alert(1)&lt;/script&gt;hi"
    fake = type("E", (), {"get": lambda self, k, d=None: payload if k == "summary" else d})()
    out = _summary(fake)
    assert "<script>" not in out
    assert "&lt;" not in out
    assert "hi" in out


def test_summary_drops_script_body():
    # Regression: with the html.parser switch, content inside <script>/<style>
    # tags is dropped entirely instead of leaking as text.
    payload = "before<script>alert(1)</script>after"
    fake = type("E", (), {"get": lambda self, k, d=None: payload if k == "summary" else d})()
    out = _summary(fake)
    assert "alert" not in out
    assert "before" in out and "after" in out


def test_summary_preserves_lt_gt_in_text():
    # Regression: the old regex strip chomped through "1 < 2 and 4 > 3"
    # because `<[^>]*>` matched across stray angle brackets.
    payload = "if 1 < 2 and 4 > 3 then ok"
    fake = type("E", (), {"get": lambda self, k, d=None: payload if k == "summary" else d})()
    out = _summary(fake)
    assert "1" in out and "2" in out and "3" in out and "4" in out and "ok" in out


def test_summary_separates_block_elements():
    # Regression: "".join(parts) merged adjacent block elements into one word.
    payload = "<div>alpha</div><div>beta</div>"
    fake = type("E", (), {"get": lambda self, k, d=None: payload if k == "summary" else d})()
    out = _summary(fake)
    assert "alpha" in out
    assert "beta" in out
    assert "alphabeta" not in out


def test_collect_skips_malformed_feed_entry(make_track, monkeypatch, capsys):
    from awsdd import collect_rss

    make_track(
        "test",
        sources_yaml="""
rss:
  - id: good
    url: https://example.com/good
  - url: https://example.com/orphan  # dict shape, no id
  - id: noisy  # dict shape, no url
  - null  # not a dict at all
""",
    )
    fetches: list[str] = []
    monkeypatch.setattr(collect_rss, "_fetch", lambda url, **k: fetches.append(url) or None)
    collect_rss.collect("test")
    assert fetches == ["https://example.com/good"]
    out = capsys.readouterr().out
    assert out.count("skipping malformed entry") == 2  # missing-key entries
    assert out.count("skipping non-dict entry") == 1  # null entry
