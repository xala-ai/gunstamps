#!/usr/bin/env python3
"""Export done movies + segment preview thumbs for the public CDN site.

For each movie, sample several analysis frames, detect the non-black content
box (letterbox/pillarbox), take a robust median crop, then apply that exact
crop to every segment thumb and scale so the long edge is 480px.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sqlite3
import statistics
import subprocess
import tarfile
from pathlib import Path

from PIL import Image

ROOT = Path("/tmp/gunstamps-export")
DB = Path("/srv/g3-1/gunstamps/gunstamps.db")
LONG_EDGE = 480
BAR_THR = 18
SAMPLE_N = 10

RATINGS_CANDIDATES = [
    Path("/srv/g3-1/gunstamps/data/official-ratings.json"),
    Path(__file__).resolve().parents[1] / "data" / "official-ratings.json",
]
OFFICIAL_RATINGS: dict = {}
for _rp in RATINGS_CANDIDATES:
    if _rp.is_file():
        try:
            OFFICIAL_RATINGS = json.loads(_rp.read_text())
            break
        except (json.JSONDecodeError, OSError):
            pass

spec = importlib.util.spec_from_file_location(
    "exapp", "/srv/g3-1/gunstamps/code/explorer/app.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

LABELS = {
    "gun": "gun",
    "explosion": "explosion",
    "death": "death",
    "kiss": "kiss",
    "scary": "scary",
    "alcohol_smoke": "alcohol/smoke",
    "nudity": "nudity",
}


def content_box(path: Path, thr: int = BAR_THR) -> tuple[int, int, int, int, float]:
    """Return x, y, w, h, aspect of non-black content inside the frame."""
    im = Image.open(path).convert("L")
    w, h = im.size
    px = im.load()
    step_x = max(1, w // 64)
    step_y = max(1, h // 64)

    y0 = 0
    while y0 < h and max(px[x, y0] for x in range(0, w, step_x)) <= thr:
        y0 += 1
    y1 = h - 1
    while y1 > y0 and max(px[x, y1] for x in range(0, w, step_x)) <= thr:
        y1 -= 1
    x0 = 0
    while x0 < w and max(
        px[x0, y] for y in range(y0, y1 + 1, max(1, (y1 - y0) // 64 or 1))
    ) <= thr:
        x0 += 1
    x1 = w - 1
    while x1 > x0 and max(
        px[x1, y] for y in range(y0, y1 + 1, max(1, (y1 - y0) // 64 or 1))
    ) <= thr:
        x1 -= 1

    cw, ch = max(1, x1 - x0 + 1), max(1, y1 - y0 + 1)
    # even dims help some encoders
    cw -= cw % 2
    ch -= ch % 2
    if cw < 2 or ch < 2:
        return 0, 0, w - w % 2, h - h % 2, w / h
    return x0, y0, cw, ch, cw / ch


def median_i(vals: list[int]) -> int:
    return int(statistics.median(vals))


def assess_movie_crop(paths: list[Path]) -> tuple[int, int, int, int, float]:
    """Robust per-movie crop from several sample frames."""
    boxes = [content_box(p) for p in paths]
    ratios = [b[4] for b in boxes]
    med_ar = statistics.median(ratios)
    # drop dark/outlier frames whose AR diverges >12% from median
    kept = [b for b in boxes if abs(b[4] - med_ar) / med_ar <= 0.12]
    if len(kept) < 3:
        kept = boxes
    x0 = median_i([b[0] for b in kept])
    y0 = median_i([b[1] for b in kept])
    x1 = median_i([b[0] + b[2] for b in kept])
    y1 = median_i([b[1] + b[3] for b in kept])
    cw = max(2, (x1 - x0) - (x1 - x0) % 2)
    ch = max(2, (y1 - y0) - (y1 - y0) % 2)
    # clamp inside first frame
    fw, fh = Image.open(paths[0]).size
    if x0 + cw > fw:
        cw = fw - x0 - (fw - x0) % 2
    if y0 + ch > fh:
        ch = fh - y0 - (fh - y0) % 2
    return x0, y0, cw, ch, cw / ch


def out_size(cw: int, ch: int) -> tuple[int, int]:
    ar = cw / ch
    if ar >= 1:
        w = LONG_EDGE
        h = max(2, int(round(LONG_EDGE / ar)))
    else:
        h = LONG_EDGE
        w = max(2, int(round(LONG_EDGE * ar)))
    return w - w % 2, h - h % 2


def write_thumb(src: Path, dest: Path, crop: tuple[int, int, int, int], size: tuple[int, int]) -> bool:
    x0, y0, cw, ch = crop
    ow, oh = size
    vf = f"crop={cw}:{ch}:{x0}:{y0},scale={ow}:{oh}:flags=lanczos"
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(src),
                "-vf",
                vf,
                "-q:v",
                "3",
                str(dest),
            ],
            check=True,
        )
        return dest.is_file()
    except Exception:
        return False


def sample_paths(con: sqlite3.Connection, mid: str) -> list[Path]:
    paths: list[Path] = []
    for r in con.execute(
        "SELECT preview_path FROM segments WHERE movie_id=? "
        "AND preview_path IS NOT NULL ORDER BY t_start",
        (mid,),
    ):
        p = Path(r["preview_path"] or "")
        if p.is_file():
            paths.append(p)
    if len(paths) < 4:
        fr = Path(f"/srv/g3-1/gunstamps/movies/{mid}/frames")
        all_f = sorted(fr.glob("f_*.jpg"))
        if all_f:
            step = max(1, len(all_f) // SAMPLE_N)
            paths = all_f[::step][:SAMPLE_N]
    if len(paths) > SAMPLE_N:
        step = len(paths) / SAMPLE_N
        paths = [paths[int(i * step)] for i in range(SAMPLE_N)]
    return paths


con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

if ROOT.exists():
    shutil.rmtree(ROOT)
(ROOT / "movies").mkdir(parents=True)
(ROOT / "thumbs").mkdir(parents=True)

index = []
for m in con.execute('SELECT * FROM movies WHERE status="done" ORDER BY title'):
    d = dict(m)
    mid = d["id"]
    samples = sample_paths(con, mid)
    if not samples:
        print(mid, "SKIP no frames")
        continue
    crop = assess_movie_crop(samples)
    size = out_size(crop[2], crop[3])
    print(
        f"{mid}: crop={crop[0]},{crop[1]} {crop[2]}x{crop[3]} "
        f"ar={crop[4]:.4f} out={size[0]}x{size[1]} samples={len(samples)}"
    )

    segs_raw = [
        dict(r)
        for r in con.execute(
            "SELECT id, category, t_start, t_end, peak_confidence, frame_count, "
            "sample_notes, summary, preview_path "
            "FROM segments WHERE movie_id=? ORDER BY t_start",
            (mid,),
        )
    ]
    safety = mod.safety_summary(
        [
            {
                "category": s["category"],
                "t_start": s["t_start"],
                "t_end": s["t_end"],
            }
            for s in segs_raw
        ],
        float(d.get("duration_s") or 0),
    )
    det_n = con.execute(
        "SELECT COUNT(*) c FROM detections WHERE movie_id=? AND COALESCE(dismissed,0)=0",
        (mid,),
    ).fetchone()["c"]

    thumb_dir = ROOT / "thumbs" / mid
    thumb_dir.mkdir(parents=True, exist_ok=True)
    segments = []
    for s in segs_raw:
        thumb_url = None
        src = Path(s["preview_path"] or "")
        if src.is_file():
            dest_name = f"{s['id']}.jpg"
            dest = thumb_dir / dest_name
            if write_thumb(src, dest, crop[:4], size):
                thumb_url = f"/thumbs/{mid}/{dest_name}"
        segments.append(
            {
                "id": s["id"],
                "category": s["category"],
                "label": LABELS.get(s["category"], s["category"]),
                "t_start": s["t_start"],
                "t_end": s["t_end"],
                "confidence": s.get("peak_confidence"),
                "frame_count": s.get("frame_count"),
                "summary": s.get("summary") or s.get("sample_notes") or "",
                "thumb": thumb_url,
            }
        )

    detail = {
        "id": mid,
        "title": d["title"],
        "year": d["year"],
        "duration_s": d["duration_s"],
        "summary": d.get("summary"),
        "segment_count": len(segments),
        "detection_count": det_n,
        "poster": f"/posters/{mid}.jpg",
        "thumb_aspect": round(crop[4], 4),
        "thumb_size": {"w": size[0], "h": size[1]},
        "safety": safety,
        "segments": segments,
    }
    official = OFFICIAL_RATINGS.get(mid) or {}
    if official.get("us") and official.get("uk"):
        detail["ratings"] = {"us": official["us"], "uk": official["uk"]}
    (ROOT / "movies" / f"{mid}.json").write_text(json.dumps(detail, indent=2))
    index.append(
        {
            k: detail[k]
            for k in (
                "id",
                "title",
                "year",
                "duration_s",
                "summary",
                "segment_count",
                "detection_count",
                "poster",
                "safety",
            )
        }
    )
    print(mid, "segs", len(segments), "thumbs", sum(1 for s in segments if s["thumb"]))

(ROOT / "movies.json").write_text(json.dumps({"version": 1, "movies": index}, indent=2))
tgz = Path("/tmp/gunstamps-export.tgz")
with tarfile.open(tgz, "w:gz") as tar:
    for p in ROOT.rglob("*"):
        if p.is_file():
            tar.add(p, arcname=str(p.relative_to(ROOT)))
print("wrote", tgz, "movies", len(index))
