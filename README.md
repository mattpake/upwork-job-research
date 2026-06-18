# Upwork Job Research

Local market research dashboard for collecting broad Upwork job data, deduplicating repeated opportunities, filtering by useful buyer signals, and exporting clean CSV analysis files.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-local-003B57?logo=sqlite&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-CSS-38BDF8?logo=tailwindcss&logoColor=white)
![License](https://img.shields.io/badge/License-private-black)

## Overview

This app runs locally and helps collect Upwork market data from configurable keywords. It uses Apify for the first scraper integration, stores normalized and raw job payloads in SQLite, merges duplicate jobs across keyword searches, and provides a clean Jinja/Tailwind dashboard for filtering, review status updates, and CSV export.

## Key Features

- Keyword scans from `config/keywords.json`
- Apify actor integration with token-based authentication
- SQLite jobs table with normalized fields plus raw JSON
- Deduplication by external job id, job URL, then title/date/client fallback
- Matched keyword merging for repeated jobs
- Premium local dashboard built with FastAPI, Jinja, Tailwind, and small JavaScript interactions
- Filters for keyword, dates, budget, hourly range, client country, payment verification, status, and text search
- Manual statuses: New, Interesting, Reviewed, Skipped, Applied
- CSV export for the current filtered result set

## Tech Stack

| Layer | Technology |
| --- | --- |
| Web server | FastAPI 0.115+, Uvicorn |
| UI | Jinja2 templates, Tailwind CDN, custom CSS, vanilla JavaScript |
| Data | SQLite through Python `sqlite3` |
| Scraper | Apify synchronous dataset API |
| Validation | Pydantic 2 |
| Tests | Pytest |

## Architecture

```mermaid
flowchart LR
    Browser[Local browser dashboard] --> FastAPI[FastAPI routes]
    FastAPI --> Config[Config loader]
    FastAPI --> Repository[SQLite repository]
    FastAPI --> Orchestrator[Scan orchestrator]
    Orchestrator --> Apify[Apify actor API]
    Orchestrator --> Normalizer[Job normalization service]
    Normalizer --> Repository
    Repository --> Export[CSV export service]
```

## Quick Start

```powershell
uv sync
Copy-Item .env.example .env
```

Edit `.env` and set `APIFY_API_TOKEN`.

```powershell
uv run uvicorn main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Environment Setup

```dotenv
APIFY_API_TOKEN=your-apify-token
UPWORK_RESEARCH_APIFY_ACTOR_ID=gio21/upwork-jobs-scraper
UPWORK_RESEARCH_RESULTS_PER_KEYWORD=50
UPWORK_RESEARCH_REQUEST_TIMEOUT_SECONDS=120
UPWORK_RESEARCH_KEYWORDS_PATH=config/keywords.json
UPWORK_RESEARCH_DATABASE_PATH=database/upwork_jobs.db
UPWORK_RESEARCH_SESSION_SECRET=replace-with-a-long-random-local-secret
```

| Variable | Description |
| --- | --- |
| `APIFY_API_TOKEN` | Required for live Upwork scans. |
| `UPWORK_RESEARCH_APIFY_ACTOR_ID` | Apify actor id. Default is `gio21/upwork-jobs-scraper`. |
| `UPWORK_RESEARCH_RESULTS_PER_KEYWORD` | Maximum jobs requested per keyword. |
| `UPWORK_RESEARCH_REQUEST_TIMEOUT_SECONDS` | HTTP timeout for one actor run. |
| `UPWORK_RESEARCH_KEYWORDS_PATH` | JSON file containing the keyword list. |
| `UPWORK_RESEARCH_DATABASE_PATH` | Local SQLite database path. |
| `UPWORK_RESEARCH_SESSION_SECRET` | Local session signing secret for scan summary messages. |

## Project Structure

```text
upwork-job-research/
+-- config/                         # Editable keyword configuration
+-- database/                       # Local SQLite database is created here
+-- docs/                           # Implementation and scraper notes
+-- src/
|   +-- core/                       # Runtime configuration
|   +-- models/                     # Pydantic job and summary models
|   +-- repositories/               # SQLite schema, filters, inserts, row mapping
|   +-- scrapers/                   # Apify scraper client
|   +-- services/                   # Normalization, scan orchestration, CSV export
|   +-- web/                        # FastAPI app, routes, templates, static assets
+-- tests/                          # Behavior tests
+-- main.py                         # Uvicorn entry point
+-- pyproject.toml                  # uv project config
```

## API Documentation

The dashboard exposes local server routes:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Render dashboard with filters and current jobs. |
| `POST` | `/scan` | Run live Apify scans for all configured keywords. |
| `POST` | `/jobs/{job_id}/status` | Update manual job status. |
| `GET` | `/export.csv` | Export the current filtered result set as CSV. |

Status update example:

```http
POST /jobs/1/status
Content-Type: application/x-www-form-urlencoded

status=Interesting
```

## Deployment

This MVP is designed for local use first.

Run locally:

```powershell
uv run uvicorn main:app --host 127.0.0.1 --port 8000
```

Future VPS cron example:

```cron
0 5 * * * cd /path/to/project && /usr/local/bin/uv run python run_scraper.py
```

## Desktop Shortcut

Create a Windows shortcut that runs:

```powershell
powershell.exe -NoExit -Command "cd D:\year_2026\upwork_job_research; uv run uvicorn main:app --host 127.0.0.1 --port 8000"
```

Then open `http://127.0.0.1:8000` in the browser.

## Apify Actor Choice

See [docs/apify-actor-comparison.md](docs/apify-actor-comparison.md) for the actor comparison and rationale.

## Testing

```powershell
uv run pytest
```

## License and Author

Private project for Rahees Ahmed.
