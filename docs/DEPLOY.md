# Deploy

Staging live: https://gunstamps.netlify.app  
Netlify already has custom domain `gunstamps.xala.ai` attached (SSL pending DNS).

## Netlify

- Site id / name: `gunstamps`
- Publish directory: `public`
- CNAME target: `gunstamps.netlify.app`

## Cloudflare (you)

1. In the `xala.ai` zone, add:
   - **Type:** CNAME  
   - **Name:** `gunstamps`  
   - **Target:** `gunstamps.netlify.app`  
   - Proxy: orange-cloud OK (same as `yellobricks.xala.ai`)
2. Wait for Netlify SSL to provision for `gunstamps.xala.ai`.

## GitHub org

If the repo is still under `csaladenes/gunstamps`, transfer to **`xala-ai/gunstamps`** in GitHub → Settings → General → Danger zone → Transfer (org create was blocked for the current PAT).

## Hardening

- No full SQLite on CDN
- Per-movie JSON only under `/api/v1/movies/{id}.json`
- Index omits heavy fields beyond safety rollup
- Later: EC2 serves the same paths with auth + rate limits
