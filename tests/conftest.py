from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from awsdd import config

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 5, 17, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def fake_tracks(tmp_path, monkeypatch):
    """Point awsdd.config.TRACKS_DIR at a temp dir so tests don't touch the real tree."""
    monkeypatch.setattr(config, "TRACKS_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def make_track(fake_tracks):
    """Factory: create a fake track dir with optional sources.yaml content."""

    def _make(name: str = "test", sources_yaml: str = "") -> Path:
        td = fake_tracks / name
        (td / "config").mkdir(parents=True, exist_ok=True)
        (td / "data" / "raw").mkdir(parents=True, exist_ok=True)
        (td / "reports").mkdir(parents=True, exist_ok=True)
        if sources_yaml:
            (td / "config" / "sources.yaml").write_text(sources_yaml)
        return td

    return _make
