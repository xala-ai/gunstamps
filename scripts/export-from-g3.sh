#!/usr/bin/env bash
# Export done-movie API snapshot from G3 into public/api/v1 + posters.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
scp "$(dirname "$0")/export-g3-remote.py" g3:/tmp/gunstamps-export-g3.py
ssh g3 '/srv/g3-1/gunstamps/venv/bin/python /tmp/gunstamps-export-g3.py'
scp g3:/tmp/gunstamps-export.tgz /tmp/gunstamps-export.tgz
rm -rf /tmp/gunstamps-export-pull
mkdir -p /tmp/gunstamps-export-pull
tar -C /tmp/gunstamps-export-pull -xzf /tmp/gunstamps-export.tgz
mkdir -p "$ROOT/public/api/v1/movies" "$ROOT/public/posters"
cp /tmp/gunstamps-export-pull/movies.json "$ROOT/public/api/v1/movies.json"
cp /tmp/gunstamps-export-pull/movies/*.json "$ROOT/public/api/v1/movies/"
# Posters: EN posters already on G3
rsync -av --include='*.jpg' --exclude='*' g3:/srv/g3-1/gunstamps/posters/ "$ROOT/public/posters/"
# Keep only posters referenced by export
python3 - <<PY
import json, pathlib
root = pathlib.Path("$ROOT")
ids = {m["id"] for m in json.loads((root/"public/api/v1/movies.json").read_text())["movies"]}
for p in (root/"public/posters").glob("*.jpg"):
    if p.stem not in ids:
        p.unlink()
print("posters kept", len(list((root/"public/posters").glob("*.jpg"))))
PY
echo "Export ready under $ROOT/public"
