#!/usr/bin/env bash
set -euo pipefail

name="${1:?usage: new-track.sh <track-name>}"
here="$(cd "$(dirname "$0")" && pwd)"
src="$here/../templates/new-track"
dst="$here/../tracks/$name"

if [ -e "$dst" ]; then
  echo "Track already exists: $dst" >&2
  exit 1
fi

mkdir -p "$dst"
cp -R "$src/." "$dst/"
# substitute placeholder in README — escape sed metachars (`&`, `\`, `|`)
# in $name so a track name like "foo&bar" doesn't trigger sed's whole-match
# substitution.
if [ -f "$dst/README.md" ]; then
  name_esc=$(printf '%s\n' "$name" | sed 's/[&|\\]/\\&/g')
  sed "s|{{TRACK}}|$name_esc|g" "$dst/README.md" > "$dst/README.md.tmp"
  mv "$dst/README.md.tmp" "$dst/README.md"
fi

echo "Created tracks/$name"
echo "Next:"
echo "  1. edit tracks/$name/config/sources.yaml"
echo "  2. add '$name' to matrix.track in .github/workflows/daily-update.yml and weekly-digest.yml"
echo "  3. add '$name' to TRACKS in web/src/lib/data.ts so the site renders it"
echo "  4. make -C tracks/$name install update"
echo "(The root Makefile auto-discovers tracks via wildcard, no edit needed.)"
