# Deploy

## Netlify

Site name: `gunstamps` (staging URL `https://gunstamps.netlify.app` until custom domain).

Deploy from repo root (`publish = public`).

## Cloudflare (you)

1. DNS for `xala.ai` zone:
   - **CNAME** `gunstamps` → `gunstamps.netlify.app` (or the site’s Netlify subdomain)
2. Proxy orange-cloud OK (same pattern as `yellobricks.xala.ai`).
3. In Netlify → Domain management → Add `gunstamps.xala.ai` → verify.

## GitHub org

If the repo is still under `csaladenes/gunstamps`, transfer to **`xala-ai/gunstamps`** in GitHub → Settings → General → Danger zone → Transfer (org create was blocked for the current PAT).

## Hardening

- No full SQLite on CDN
- Per-movie JSON only under `/api/v1/movies/{id}.json`
- Index omits heavy fields beyond safety rollup
- Later: EC2 serves the same paths with auth + rate limits
