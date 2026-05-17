#!/usr/bin/env bash
# Trim large or stale per-track artefacts.
#   - data/raw/*.json : keep last 30 days
#   - reports/daily/*.md : keep last 60 days
# weekly reports and normalized/scored snapshots are kept forever.
set -euo pipefail

track_dir="${1:?usage: prune.sh <track-dir>}"
cd "$track_dir"

if [ -d data/raw ]; then
  find data/raw -type f -name '*.json' -mtime +30 -print -delete || true
fi
if [ -d reports/daily ]; then
  find reports/daily -type f -name '*.md' -mtime +60 -print -delete || true
fi
