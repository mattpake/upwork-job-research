# Apify Actor Comparison

This MVP uses `gio21/upwork-jobs-scraper` by default because its current public documentation is the closest fit for broad keyword-based market research.

## Compared Actors

| Actor | Input fit | Output fit | Cost signal | Stability signal | Decision |
| --- | --- | --- | --- | --- | --- |
| `gio21/upwork-jobs-scraper` | `query` plus `max_jobs`, matching one keyword scan per run | Returns job id, title, description, budget, skills, proposals, client country, spend, verified status, and URL | Listed at $1.50 per 1,000 jobs | Recently modified, small but focused usage | Default actor |
| `neatrat/upwork-job-scraper` | API docs exist and it supports custom searches | Rich fields and authenticated managed setup | Listed from $3.20 per 1,000 jobs | Larger usage and rating, but recent issue reports mention zero-result runs | Supported by normalizer, not default |
| `upwork-vibe/upwork-job-scraper` | Supports keyword filters under `includeKeywords.*` | Broad public job fields and optional paid addons | Listed from $4.50 per 1,000 job results | Fast issue response and good rating | Supported by input builder, not default |

## Why `gio21/upwork-jobs-scraper`

- The input shape is simple and maps cleanly to this app: one configured keyword becomes one actor run.
- The output includes the fields this MVP needs for dedupe, filtering, CSV export, and later analysis.
- It does not require Upwork login credentials or cookies.
- It is cheaper than the two named PRD candidates based on the current public pricing shown on Apify.

The scraper layer is isolated in `src/scrapers/apify_upwork_scraper.py`, and normalization lives in `src/services/job_normalization_service.py`, so the default actor can be changed with `UPWORK_RESEARCH_APIFY_ACTOR_ID` without rewriting the dashboard.
