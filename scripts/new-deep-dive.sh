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
sed -e "s/{{TRACK}}/$track/g" -e "s/{{TOPIC}}/$topic/g" -e "s/{{DATE}}/$(date -u +%Y-%m-%d)/g" "$src" > "$dst"
echo "Created $dst"
