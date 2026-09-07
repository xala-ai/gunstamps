#!/usr/bin/env bash
# Export done-movie API snapshot + 16:9 thumbs from G3 into public/.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
scp "$(dirname "$0")/export-g3-rich.py" g3:/tmp/gunstamps-export-rich.py
ssh g3 '/srv/g3-1/gunstamps/venv/bin/python /tmp/gunstamps-export-rich.py'
scp g3:/tmp/gunstamps-export.tgz /tmp/gunstamps-export.tgz
rm -rf /tmp/gunstamps-export-pull
mkdir -p /tmp/gunstamps-export-pull
tar -C /tmp/gunstamps-export-pull -xzf /tmp/gunstamps-export.tgz
mkdir -p "$ROOT/public/api/v1/movies" "$ROOT/public/posters" "$ROOT/public/thumbs"
cp /tmp/gunstamps-export-pull/movies.json "$ROOT/public/api/v1/movies.json"
cp /tmp/gunstamps-export-pull/movies/*.json "$ROOT/public/api/v1/movies/"
rm -rf "$ROOT/public/thumbs"
cp -a /tmp/gunstamps-export-pull/thumbs "$ROOT/public/thumbs"
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
print("thumbs", sum(1 for _ in (root/"public/thumbs").rglob("*.jpg")))
PY
# Mirror to G3 public preview (:8787)
rsync -az --delete "$ROOT/public/" g3:/srv/g3-1/gunstamps/public/
echo "Export ready under $ROOT/public (+ synced to g3 public/)"
