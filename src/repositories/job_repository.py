import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.models.job_models import NormalizedUpworkJob, StoredUpworkJob, UpsertJobsSummary
from src.repositories.job_database_schema import JOB_TABLE_INDEXES, JOB_TABLE_SCHEMA
from src.repositories.job_filter_builder import appendJobFilterClauses
from src.repositories.job_insert_mapper import INSERT_JOB_SQL, buildJobInsertParameters
from src.repositories.job_row_mapper import convertJobRowToStoredJob


class JobRepository:
    """SQLite repository for Upwork job records."""

    def __init__(self, databasePath: Path) -> None:
        self.databasePath = databasePath

    def initializeDatabase(self) -> None:
        """Create database tables and indexes when missing."""

        self.databasePath.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as databaseConnection:
            databaseConnection.execute(JOB_TABLE_SCHEMA)
            for indexStatement in JOB_TABLE_INDEXES:
                databaseConnection.execute(indexStatement)

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
        appendJobFilterClauses(queryClauses, queryParameters, activeFilters)
        whereClause = f" WHERE {' AND '.join(queryClauses)}" if queryClauses else ""
        selectQuery = f"SELECT * FROM jobs{whereClause} ORDER BY scraped_at DESC, id DESC"
        with self._connect() as databaseConnection:
            jobRows = databaseConnection.execute(selectQuery, queryParameters).fetchall()
        return [convertJobRowToStoredJob(jobRow) for jobRow in jobRows]

    def getJobById(self, jobId: int) -> StoredUpworkJob:
        """Load one stored job by database id."""

        self.initializeDatabase()
        with self._connect() as databaseConnection:
            jobRow = databaseConnection.execute("SELECT * FROM jobs WHERE id = ?", (jobId,)).fetchone()
        if jobRow is None:
            raise ValueError(f"Job not found: {jobId}")
        return convertJobRowToStoredJob(jobRow)

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
        insertCursor = databaseConnection.execute(INSERT_JOB_SQL, buildJobInsertParameters(normalizedJob))
        return int(insertCursor.lastrowid)

def _mergeUniqueValues(existingValues: list[str], newValues: list[str]) -> list[str]:
    mergedValues: list[str] = []
    seenValueKeys: set[str] = set()
    for candidateValue in [*existingValues, *newValues]:
        valueKey = candidateValue.casefold()
        if valueKey not in seenValueKeys:
            mergedValues.append(candidateValue)
            seenValueKeys.add(valueKey)
    return mergedValues


def _chooseRicherRawJson(existingRawJson: dict[str, Any], newRawJson: dict[str, Any]) -> dict[str, Any]:
    return newRawJson if len(json.dumps(newRawJson)) > len(json.dumps(existingRawJson)) else existingRawJson
