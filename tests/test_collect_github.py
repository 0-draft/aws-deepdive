from __future__ import annotations

import json

from awsdd.collect_github import release_to_item

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
