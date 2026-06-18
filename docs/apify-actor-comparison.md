# Apify Actor Comparison

This MVP uses `neatrat/upwork-job-scraper` by default because the local `api_docs.md` file supplied for this project contains that actor's endpoint and input schema.

## Compared Actors

| Actor | Input fit | Output fit | Cost signal | Stability signal | Decision |
| --- | --- | --- | --- | --- | --- |
| `neatrat/upwork-job-scraper` | Local `api_docs.md` documents `query`, `page`, `pagesToScrape`, `perPage`, and `sort` | Rich fields and managed setup | Listed from $3.20 per 1,000 jobs | Larger usage and rating, but live reliability still depends on Apify actor state | Default actor |
| `gio21/upwork-jobs-scraper` | `query` plus `max_jobs`, matching one keyword scan per run | Returns job id, title, description, budget, skills, proposals, client country, spend, verified status, and URL | Listed at $1.50 per 1,000 jobs | Recently modified, small but focused usage | Supported fallback |
| `upwork-vibe/upwork-job-scraper` | Supports keyword filters under `includeKeywords.*` | Broad public job fields and optional paid addons | Listed from $4.50 per 1,000 job results | Fast issue response and good rating | Supported by input builder, not default |

## Why `neatrat/upwork-job-scraper`

- The local API docs are for this actor, so the implementation should follow that contract first.
- The input supports one configured keyword per run with `perPage` and `sort: newest`.
- Optional filters/cookies from the docs are deliberately not sent by default because the PRD says broad market collection and no Upwork login.
- The scraper layer still supports changing actors through `UPWORK_RESEARCH_APIFY_ACTOR_ID`.

The scraper layer is isolated in `src/scrapers/apify_upwork_scraper.py`, and normalization lives in `src/services/job_normalization_service.py`, so the default actor can be changed with `UPWORK_RESEARCH_APIFY_ACTOR_ID` without rewriting the dashboard.
