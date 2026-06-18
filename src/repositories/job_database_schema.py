JOB_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_job_id TEXT,
    job_url TEXT,
    title TEXT NOT NULL,
    description TEXT,
    search_keyword TEXT NOT NULL,
    matched_keywords TEXT NOT NULL,
    skills TEXT NOT NULL,
    budget_type TEXT,
    fixed_budget REAL,
    hourly_min REAL,
    hourly_max REAL,
    client_country TEXT,
    client_spent TEXT,
    client_rating REAL,
    payment_verified INTEGER,
    proposals_count TEXT,
    posted_at TEXT,
    scraped_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    status TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    client_hires TEXT,
    client_jobs_posted TEXT,
    client_avg_hourly_rate_paid TEXT,
    client_total_reviews TEXT,
    job_duration TEXT,
    experience_level TEXT,
    connects_required TEXT,
    category TEXT,
    subcategory TEXT
);
"""


JOB_TABLE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_jobs_external_id ON jobs(external_job_id)",
    "CREATE INDEX IF NOT EXISTS idx_jobs_url ON jobs(job_url)",
    "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)",
    "CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON jobs(scraped_at)",
]
