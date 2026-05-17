from __future__ import annotations

import json

from awsdd.collect_github import _next_url, release_to_item

from .conftest import FIXTURES, NOW


def _releases():
    return json.loads((FIXTURES / "release_sample.json").read_text())


def test_release_to_item_basic():
    rel = _releases()[0]
    item = release_to_item(rel, "aws/aws-cli", "releases", NOW)
    assert item is not None
    assert item["source"] == "github:aws/aws-cli"
    assert item["source_kind"] == "github"
    assert item["title"] == "2.99.0"
    assert "Breaking change" in item["summary"]
    assert item["tags"] == []


def test_prerelease_is_tagged():
    rel = _releases()[1]
    item = release_to_item(rel, "aws/aws-cli", "releases", NOW)
    assert "prerelease" in item["tags"]


def test_draft_is_dropped():
    rel = _releases()[2]
    assert release_to_item(rel, "aws/aws-cli", "releases", NOW) is None


def test_falls_back_to_tag_name_when_no_name():
    rel = {
        "html_url": "https://github.com/x/y/releases/tag/v1",
        "tag_name": "v1",
        "body": "",
        "published_at": "2026-01-01T00:00:00Z",
    }
    item = release_to_item(rel, "x/y", "releases", NOW)
    assert item["title"] == "v1"


def test_next_url_parses_link_header():
    link = (
        '<https://api.github.com/repos/x/y/releases?page=2>; rel="next", '
        '<https://api.github.com/repos/x/y/releases?page=5>; rel="last"'
    )
    assert _next_url(link) == "https://api.github.com/repos/x/y/releases?page=2"


def test_next_url_returns_none_when_no_next():
    link = '<https://api.github.com/repos/x/y/releases?page=5>; rel="last"'
    assert _next_url(link) is None


def test_next_url_handles_missing_header():
    assert _next_url(None) is None
    assert _next_url("") is None


def test_collect_skips_malformed_repo_entry(make_track, monkeypatch, capsys):
    from awsdd import collect_github

    make_track(
        "test",
        sources_yaml="""
github:
  - repo: aws/aws-cli
  - per_page: 5  # no repo key (dict shape but missing repo)
  - null  # not a dict at all
  - "just a string"  # also not a dict
""",
    )
    calls: list[str] = []
    monkeypatch.setattr(collect_github, "_get_all", lambda path: calls.append(path) or [])
    collect_github.collect("test")
    # only the well-formed entry is fetched
    assert calls == ["/repos/aws/aws-cli/releases?per_page=50"]
    out = capsys.readouterr().out
    assert out.count("skipping non-dict entry") == 2
    assert out.count("skipping malformed entry") == 1
