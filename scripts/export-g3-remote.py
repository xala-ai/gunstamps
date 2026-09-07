#!/usr/bin/env python3
"""Run on G3: export done movies to /tmp/gunstamps-export.tgz"""
import json
import importlib.util
import sqlite3
import tarfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "exapp", "/srv/g3-1/gunstamps/code/explorer/app.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

con = sqlite3.connect("/srv/g3-1/gunstamps/gunstamps.db")
con.row_factory = sqlite3.Row
out = Path("/tmp/gunstamps-export")
(out / "movies").mkdir(parents=True, exist_ok=True)

movies = []
for m in con.execute('SELECT * FROM movies WHERE status="done" ORDER BY title'):
    d = dict(m)
    safety = mod.safety_summary_for_movie(con, m)
    segs = [
        dict(r)
        for r in con.execute(
            "SELECT category, t_start, t_end, peak_confidence, summary, sample_notes "
            "FROM segments WHERE movie_id=? ORDER BY t_start",
            (d["id"],),
        )
    ]
    det_n = con.execute(
        "SELECT COUNT(*) c FROM detections WHERE movie_id=? AND COALESCE(dismissed,0)=0",
        (d["id"],),
    ).fetchone()["c"]
    detail = {
        "id": d["id"],
        "title": d["title"],
        "year": d["year"],
        "duration_s": d["duration_s"],
        "summary": d.get("summary"),
        "segment_count": len(segs),
        "detection_count": det_n,
        "poster": f"/posters/{d['id']}.jpg",
        "safety": {
            "rag": safety["rag"],
            "rag_label": safety["rag_label"],
            "pct": safety["pct"],
            "pct_label": safety["pct_label"],
            "unsafe_minutes": safety["unsafe_minutes"],
            "total_minutes": safety["total_minutes"],
            "bar": safety["bar"],
            "headline": safety["headline"],
        },
        "segments": [
            {
                "category": s["category"],
                "t_start": s["t_start"],
                "t_end": s["t_end"],
                "confidence": s.get("peak_confidence"),
                "summary": s.get("summary") or s.get("sample_notes"),
            }
            for s in segs
        ],
    }
    (out / "movies" / f"{d['id']}.json").write_text(json.dumps(detail, indent=2))
    movies.append({k: detail[k] for k in (
        "id", "title", "year", "duration_s", "summary",
        "segment_count", "detection_count", "poster", "safety",
    )})

(out / "movies.json").write_text(json.dumps({"version": 1, "movies": movies}, indent=2))
tgz = Path("/tmp/gunstamps-export.tgz")
with tarfile.open(tgz, "w:gz") as tar:
    for p in out.rglob("*"):
        if p.is_file():
            tar.add(p, arcname=str(p.relative_to(out)))
print("wrote", tgz, "movies", len(movies))
