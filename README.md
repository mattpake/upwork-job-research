# Upwork Job Research Dashboard

A local research tool that scrapes Upwork jobs using Apify, automatically merges duplicates, and provides a clean dashboard for filtering and reviewing market data.

## Quick Start

1. **Install dependencies** using `uv`:
   ```bash
   uv sync
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and add your `APIFY_API_TOKEN`.

3. **Set your keywords**:
   Edit `config/keywords.json` to define your target search terms.

4. **Start the application**:
   ```bash
   uv run main.py
   ```

5. **Open the dashboard**:
   Navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

## Key Features

- **Automated Scraping**: Fetches jobs via Apify for all your configured keywords.
- **Deduplication**: Automatically merges identical jobs found across different keyword searches.
- **Dashboard Review**: Filter jobs by budget, client location, hourly rates, and keywords.
- **Workflow Management**: Mark jobs as *New*, *Interesting*, *Reviewed*, *Skipped*, or *Applied*.
- **CSV Export**: Export your filtered view for external analysis.

## Configuration

* **Keywords**: Manage your search terms in `config/keywords.json`.
* **Application Settings**: Default settings (like API timeouts and concurrency) live in `config/settings.json`.
* **Secrets & Overrides**: Use your `.env` file to set your API token and override any default settings (e.g., `UPWORK_RESEARCH_RESULTS_PER_KEYWORD`).
