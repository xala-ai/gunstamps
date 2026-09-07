# GunStamps

Parental guidance stamps for kids’ movies (guns, explosions, scary scenes, alcohol/smoke, nudity, …).

**Live:** https://gunstamps.xala.ai  
**Repo:** https://github.com/xala-ai/gunstamps

## Two modes only

| Mode | What | Where |
|------|------|--------|
| **Simple** | Catalog: poster, mix bar, summary, segment count, search | `/` on the live site |
| **Expert** | Movie detail: summary + %, mix bar, timeline with thumbs, flagged-scenes table | `/movie.html?id=…` |

No other public UI variants. Pipeline tooling is **Dev** only (not a product mode).

## Architecture

| Layer | Role |
|--------|------|
| Netlify CDN | Simple + Expert UI + `/api/v1` snapshot |
| G3 `:8787/` | **Same `public/` tree** as Netlify (preview before deploy) |
| G3 `:8787/dev` | Ops / pipeline (former `/expert` and `/ops`) |
| G3 `:8790` | Read API over SQLite |
| EC2 (later) | Canonical API + DB |

## Preview before deploy

Always exercise the **exact** `public/` publish tree first — that is what Netlify serves.

**Laptop (fast):**

```bash
cd public && python3 -m http.server 8788
# open http://127.0.0.1:8788/
```

**G3 Tailscale (shared preview of the same tree):**

- Public app: `http://100.116.141.47:8787/`
- Dev / pipeline: `http://100.116.141.47:8787/dev`

After changing `public/`, rsync to G3 so Tailscale matches laptop:

```bash
rsync -az --delete public/ g3:/srv/g3-1/gunstamps/public/
```

## Export / deploy

```bash
./scripts/export-from-g3.sh   # refresh JSON + thumbs from G3 into public/
# preview locally (or on :8787), then commit + Netlify deploy (see docs/DEPLOY.md)
```
