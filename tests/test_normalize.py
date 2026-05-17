from __future__ import annotations

import json

from awsdd.normalize import normalize


def _raw_item(id_: str, **overrides) -> dict:
    base = {
        "id": id_,
        "track": "test",
        "source": "rss:src",
        "source_kind": "rss",
        "url": f"https://example.com/{id_}",
        "title": "t",
        "summary": "s",
        "published_at": "2026-05-15T00:00:00+00:00",
        "fetched_at": "2026-05-15T00:00:00+00:00",
        "tags": [],
        "severity": None,
    }
    base.update(overrides)
    return base


def test_dedupes_by_id_keeping_earliest_fetched_at(make_track):
    td = make_track("test")
    raw = td / "data" / "raw"
    (raw / "a.json").write_text(
        json.dumps([_raw_item("x", fetched_at="2026-05-15T00:00:00+00:00")])
    )
    (raw / "b.json").write_text(
        json.dumps([_raw_item("x", fetched_at="2026-05-17T00:00:00+00:00")])
    )

    normalize("test")

    out = json.loads((td / "data" / "normalized.json").read_text())
    assert len(out) == 1
    assert out[0]["fetched_at"] == "2026-05-15T00:00:00+00:00"


def test_sorts_by_published_at_desc(make_track):
    td = make_track("test")
    raw = td / "data" / "raw"
    (raw / "a.json").write_text(
        json.dumps(
            [
                _raw_item("old", published_at="2026-01-01T00:00:00+00:00"),
                _raw_item("new", published_at="2026-05-15T00:00:00+00:00"),
            ]
        )
    )

    normalize("test")

    out = json.loads((td / "data" / "normalized.json").read_text())
    assert [it["id"] for it in out] == ["new", "old"]


def test_missing_raw_dir_writes_empty(make_track):
    td = make_track("test")
    normalize("test")
    out = json.loads((td / "data" / "normalized.json").read_text())
    assert out == []
