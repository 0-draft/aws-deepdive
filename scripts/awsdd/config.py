from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
TRACKS_DIR = ROOT / "tracks"


def track_dir(name: str) -> Path:
    return TRACKS_DIR / name


def load_sources(track: str) -> dict:
    p = track_dir(track) / "config" / "sources.yaml"
    if not p.exists():
        return {}
    loaded = yaml.safe_load(p.read_text()) or {}
    # If a sources.yaml is malformed and its root is a list / scalar, downstream
    # .get() calls would crash. Coerce to {} so the track is just a no-op.
    return loaded if isinstance(loaded, dict) else {}
