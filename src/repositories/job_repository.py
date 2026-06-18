import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.models.job_models import NormalizedUpworkJob, StoredUpworkJob, UpsertJobsSummary


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


class JobRepository:
    """SQLite repository for Upwork job records."""

    def __init__(self, databasePath: Path) -> None:
        self.databasePath = databasePath

    def initializeDatabase(self) -> None:
        """Create database tables and indexes when missing."""

        self.databasePath.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as databaseConnection:
            databaseConnection.execute(JOB_TABLE_SCHEMA)
            databaseConnection.execute("CREATE INDEX IF NOT EXISTS idx_jobs_external_id ON jobs(external_job_id)")
            databaseConnection.execute("CREATE INDEX IF NOT EXISTS idx_jobs_url ON jobs(job_url)")
            databaseConnection.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
            databaseConnection.execute("CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON jobs(scraped_at)")

    def upsertNormalizedJobs(self, normalizedJobs: list[NormalizedUpworkJob]) -> UpsertJobsSummary:
        """Insert new jobs and merge duplicate keyword matches."""

        self.initializeDatabase()
        newJobsAdded = 0
        duplicatesFound = 0
        insertedJobIds: list[int] = []
        with self._connect() as databaseConnection:
            for normalizedJob in normalizedJobs:
                duplicateJobRow = self._findDuplicateJob(databaseConnection, normalizedJob)
                if duplicateJobRow:
                    duplicatesFound += 1
                    self._mergeDuplicateJob(databaseConnection, duplicateJobRow, normalizedJob)
                    continue

                insertedJobId = self._insertJob(databaseConnection, normalizedJob)
                insertedJobIds.append(insertedJobId)
                newJobsAdded += 1

        return UpsertJobsSummary(
            totalJobsFetched=len(normalizedJobs),
            newJobsAdded=newJobsAdded,
            duplicatesFound=duplicatesFound,
            insertedJobIds=insertedJobIds,
        )

    def listJobs(self, filters: dict[str, Any] | None = None) -> list[StoredUpworkJob]:
        """List stored jobs with optional dashboard filters."""

        self.initializeDatabase()
        queryClauses: list[str] = []
        queryParameters: list[Any] = []
        activeFilters = filters or {}
        self._appendFilterClauses(queryClauses, queryParameters, activeFilters)
        whereClause = f" WHERE {' AND '.join(queryClauses)}" if queryClauses else ""
        selectQuery = f"SELECT * FROM jobs{whereClause} ORDER BY scraped_at DESC, id DESC"
        with self._connect() as databaseConnection:
            jobRows = databaseConnection.execute(selectQuery, queryParameters).fetchall()
        return [self._rowToStoredJob(jobRow) for jobRow in jobRows]

    def getJobById(self, jobId: int) -> StoredUpworkJob:
        """Load one stored job by database id."""

        self.initializeDatabase()
        with self._connect() as databaseConnection:
            jobRow = databaseConnection.execute("SELECT * FROM jobs WHERE id = ?", (jobId,)).fetchone()
        if jobRow is None:
            raise ValueError(f"Job not found: {jobId}")
        return self._rowToStoredJob(jobRow)

    def updateJobStatus(self, jobId: int, status: str) -> None:
        """Update the manual dashboard status for one job."""

        self.initializeDatabase()
        with self._connect() as databaseConnection:
            updateCursor = databaseConnection.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, jobId))
        if updateCursor.rowcount == 0:
            raise ValueError(f"Job not found: {jobId}")

    def _connect(self) -> sqlite3.Connection:
        databaseConnection = sqlite3.connect(self.databasePath)
        databaseConnection.row_factory = sqlite3.Row
        return databaseConnection

    def _findDuplicateJob(
        self,
        databaseConnection: sqlite3.Connection,
        normalizedJob: NormalizedUpworkJob,
    ) -> sqlite3.Row | None:
        if normalizedJob.externalJobId:
            matchedRow = databaseConnection.execute(
                "SELECT * FROM jobs WHERE external_job_id = ?",
                (normalizedJob.externalJobId,),
            ).fetchone()
            if matchedRow:
                return matchedRow
        if normalizedJob.jobUrl:
            matchedRow = databaseConnection.execute(
                "SELECT * FROM jobs WHERE job_url = ?",
                (normalizedJob.jobUrl,),
            ).fetchone()
            if matchedRow:
                return matchedRow
        return databaseConnection.execute(
            """
            SELECT * FROM jobs
            WHERE lower(title) = lower(?) AND COALESCE(posted_at, '') = COALESCE(?, '')
            AND COALESCE(client_country, '') = COALESCE(?, '')
            """,
            (normalizedJob.title, normalizedJob.postedAt, normalizedJob.clientCountry),
        ).fetchone()

    def _mergeDuplicateJob(
        self,
        databaseConnection: sqlite3.Connection,
        duplicateJobRow: sqlite3.Row,
        normalizedJob: NormalizedUpworkJob,
    ) -> None:
        existingMatchedKeywords = json.loads(duplicateJobRow["matched_keywords"])
        mergedMatchedKeywords = _mergeUniqueValues(existingMatchedKeywords, normalizedJob.matchedKeywords)
        mergedRawJson = _chooseRicherRawJson(json.loads(duplicateJobRow["raw_json"]), normalizedJob.rawJson)
        databaseConnection.execute(
            "UPDATE jobs SET matched_keywords = ?, raw_json = ?, last_seen_at = ? WHERE id = ?",
            (
                json.dumps(mergedMatchedKeywords),
                json.dumps(mergedRawJson, ensure_ascii=True),
                datetime.now(UTC).isoformat(),
                duplicateJobRow["id"],
            ),
        )

    def _insertJob(self, databaseConnection: sqlite3.Connection, normalizedJob: NormalizedUpworkJob) -> int:
        insertCursor = databaseConnection.execute(
            """
            INSERT INTO jobs (
                external_job_id, job_url, title, description, search_keyword, matched_keywords,
                skills, budget_type, fixed_budget, hourly_min, hourly_max, client_country,
                client_spent, client_rating, payment_verified, proposals_count, posted_at,
                scraped_at, last_seen_at, status, raw_json, client_hires, client_jobs_posted,
                client_avg_hourly_rate_paid, client_total_reviews, job_duration, experience_level,
                connects_required, category, subcategory
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            self._buildInsertParameters(normalizedJob),
        )
        return int(insertCursor.lastrowid)

    def _buildInsertParameters(self, normalizedJob: NormalizedUpworkJob) -> tuple[Any, ...]:
        return (
            normalizedJob.externalJobId,
            normalizedJob.jobUrl,
            normalizedJob.title,
            normalizedJob.description,
            normalizedJob.searchKeyword,
            json.dumps(normalizedJob.matchedKeywords),
            json.dumps(normalizedJob.skills),
            normalizedJob.budgetType,
            normalizedJob.fixedBudget,
            normalizedJob.hourlyMin,
            normalizedJob.hourlyMax,
            normalizedJob.clientCountry,
            normalizedJob.clientSpent,
            normalizedJob.clientRating,
            int(normalizedJob.paymentVerified) if normalizedJob.paymentVerified is not None else None,
            normalizedJob.proposalsCount,
            normalizedJob.postedAt,
            normalizedJob.scrapedAt,
            normalizedJob.lastSeenAt,
            normalizedJob.status,
            json.dumps(normalizedJob.rawJson, ensure_ascii=True),
            normalizedJob.clientHires,
            normalizedJob.clientJobsPosted,
            normalizedJob.clientAvgHourlyRatePaid,
            normalizedJob.clientTotalReviews,
            normalizedJob.jobDuration,
            normalizedJob.experienceLevel,
            normalizedJob.connectsRequired,
            normalizedJob.category,
            normalizedJob.subcategory,
        )

