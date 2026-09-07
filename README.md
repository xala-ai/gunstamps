# GunStamps

Parental guidance stamps for kids’ movies (guns, explosions, scary scenes, alcohol/smoke, nudity, …).

- **Site (staging):** https://gunstamps.netlify.app
- **Custom domain (pending Cloudflare DNS):** https://gunstamps.xala.ai
- **API shape:** [`/api/v1/movies.json`](public/api/v1/movies.json) · OpenAPI [`public/openapi.yaml`](public/openapi.yaml)
- **Issues / roadmap:** use GitHub Issues on this repo
- **Note:** repo is currently `csaladenes/gunstamps` — transfer to `xala-ai/gunstamps` in GitHub Settings (org create blocked for the agent PAT)

## Architecture (day 1)

| Layer | Role |
|--------|------|
| GitHub | Roadmap, issues, plugin repos, this static site source |
| Netlify CDN | Public UI + versioned `/api/v1/*.json` snapshot |
| G3 (private) | Analysis worker + SQLite source of truth (not public) |
| EC2 (later) | Canonical API + DB; CDN keeps the UI |

Static JSON on the CDN is a **publish snapshot**, not the product database. Clients (web, Kodi, browser extensions) should call the versioned API paths so we can swap in EC2 without rewriting plugins.

## Local preview

```bash
cd public && python3 -m http.server 8788
```

## Export snapshot from G3

```bash
./scripts/export-from-g3.sh
```

## Domain

Reserve **gunstamps.xala.ai** in Cloudflare → CNAME to the Netlify site hostname (see `docs/DEPLOY.md`).
