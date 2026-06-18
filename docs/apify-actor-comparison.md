# Apify Actor Comparison

This MVP uses `upwork-vibe/upwork-job-scraper` by default because the current local `api_docs.md` file supplied for this project contains that actor's endpoint and Python SDK input schema.

## Compared Actors

| Actor | Input fit | Output fit | Cost signal | Stability signal | Decision |
| --- | --- | --- | --- | --- | --- |
| `upwork-vibe/upwork-job-scraper` | Current local `api_docs.md` documents `includeKeywords.*`, budget, client, vendor, addon, notification, and `limit` fields | Broad public job fields and optional paid addons | Listed from $4.50 per 1,000 job results | Good match for supplied SDK snippet | Default actor |
| `neatrat/upwork-job-scraper` | Older docs used `query`, `page`, `pagesToScrape`, `perPage`, and `sort` | Rich fields and managed setup | Listed from $3.20 per 1,000 jobs | No longer matches the supplied docs | Supported fallback |
| `gio21/upwork-jobs-scraper` | Uses `query` plus `max_jobs` | Returns job id, title, description, budget, skills, proposals, client country, spend, verified status, and URL | Listed at $1.50 per 1,000 jobs | Smaller focused actor | Supported fallback |

## Why `upwork-vibe/upwork-job-scraper`

- The current local API docs and Python SDK example are for this actor.
- The input supports one configured keyword per run through `includeKeywords.keywords`.
- The default payload keeps broad collection enabled and avoids login/cookie fields.
- The scraper uses the official `apify-client` Python SDK instead of hand-written HTTP calls.

The scraper layer is isolated in `src/scrapers/apify_upwork_scraper.py`, and normalization lives in `src/services/job_normalization_service.py`, so the default actor can be changed with `UPWORK_RESEARCH_APIFY_ACTOR_ID` without rewriting the dashboard.
