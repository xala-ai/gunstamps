# GunStamps

Parental guidance stamps for kids’ movies (guns, explosions, scary scenes, alcohol/smoke, nudity, …).

**Live:** https://gunstamps.xala.ai  
**Repo:** https://github.com/xala-ai/gunstamps

## Two modes only

| Mode | What | Where |
|------|------|--------|
| **Simple** | Catalog: poster, mix bar, summary, segment count, search | `/` on the live site |
| **Expert** | Movie detail: summary + %, mix bar, timeline with thumbs, flagged-scenes table | `/movie.html?id=…` |

No other public UI variants. Internal analysis tooling on G3 (`:8787/ops`) is ops-only, not a product mode.

## Architecture

| Layer | Role |
|--------|------|
| Netlify CDN | Simple + Expert UI + `/api/v1` snapshot |
| G3 | Analysis worker, SQLite, read API `:8790`, ops UI `:8787/ops` |
| EC2 (later) | Canonical API + DB |

## Local preview

```bash
cd public && python3 -m http.server 8788
```

## Export / deploy

```bash
./scripts/export-from-g3.sh   # refresh JSON + thumbs from G3
# then commit + Netlify deploy (see docs/DEPLOY.md)
```
