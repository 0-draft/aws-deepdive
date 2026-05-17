from __future__ import annotations

from awsdd.score import SEVERITY_WEIGHT, score_item

from .conftest import NOW

SOURCES_IAM = {
    "keywords": {
        "primary": ["roles-anywhere", "trust-anchor"],
        "secondary": ["iam", "sts"],
    },
    "source_weights": {
        "default": 1.0,
        "rss:aws-iam-release-notes": 3.0,
        "rss:aws-whats-new": 1.5,
    },
}


def _item(**overrides):
    base = {
        "published_at": NOW.isoformat(),
        "title": "",
        "summary": "",
        "source": "rss:default",
        "severity": None,
    }
    base.update(overrides)
    return base


def test_fresh_keyword_match_on_trusted_source_scores_high():
    # keywords are matched as substrings, so the title must contain the literal hyphenated form.
    item = _item(
        title="roles-anywhere now supports trust-anchor improvements",
        source="rss:aws-iam-release-notes",
    )
    b = score_item(item, SOURCES_IAM, NOW)
    # 2 primary hits * 2.0 = 4.0 keyword, source_w=3.0, kw_signal=12.0
    # freshness*2 ≈ 2.0 (same day)
    assert b["keyword"] >= 4.0
    assert b["source"] == 3.0
    assert b["total"] > 13.0


def test_no_keyword_match_only_gets_freshness_baseline():
    item = _item(title="Generic announcement", source="rss:aws-whats-new")
    b = score_item(item, SOURCES_IAM, NOW)
    # keyword_signal = 0 * 1.5 = 0; total ≈ freshness only
    assert b["keyword_signal"] == 0.0
    assert b["total"] < 2.5


def test_secondary_keyword_gets_partial_credit():
    item = _item(title="IAM something", source="rss:aws-whats-new")
    b = score_item(item, SOURCES_IAM, NOW)
    # one secondary hit: 0.5 * source_w 1.5 = 0.75
    assert 0.5 <= b["keyword_signal"] <= 1.0


def test_old_items_have_negligible_freshness():
    item = _item(
        published_at="2025-01-01T00:00:00+00:00",
        title="iam roles-anywhere",
        source="rss:aws-iam-release-notes",
    )
    b = score_item(item, SOURCES_IAM, NOW)
    assert b["freshness"] < 0.05  # ~500 days, exp(-500/14) tiny


def test_severity_added_for_critical():
    item = _item(severity="critical")
    b = score_item(item, SOURCES_IAM, NOW)
    assert b["severity"] == SEVERITY_WEIGHT["critical"]


def test_unknown_severity_zero():
    item = _item(severity="info")
    b = score_item(item, SOURCES_IAM, NOW)
    assert b["severity"] == 0.0
