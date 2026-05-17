#!/usr/bin/env bash
set -euo pipefail

track="${1:?usage: new-deep-dive.sh <track> <topic>}"
topic="${2:?usage: new-deep-dive.sh <track> <topic>}"
here="$(cd "$(dirname "$0")" && pwd)"
src="$here/../templates/deep-dive.md"
dst_dir="$here/../tracks/$track/deep-dives"
dst="$dst_dir/$topic.md"

if [ ! -d "$here/../tracks/$track" ]; then
  echo "Track not found: tracks/$track" >&2
  exit 1
fi
if [ -e "$dst" ]; then
  echo "Already exists: $dst" >&2
  exit 1
fi

mkdir -p "$dst_dir"
# Escape sed metachars (`&`, `\`, `|`) in the substitution values so a track
# or topic that contains them doesn't trigger sed's whole-match replacement.
track_esc=$(printf '%s\n' "$track" | sed 's/[&|\\]/\\&/g')
topic_esc=$(printf '%s\n' "$topic" | sed 's/[&|\\]/\\&/g')
date_str=$(date -u +%Y-%m-%d)
sed -e "s|{{TRACK}}|$track_esc|g" -e "s|{{TOPIC}}|$topic_esc|g" -e "s|{{DATE}}|$date_str|g" "$src" > "$dst"
echo "Created $dst"
