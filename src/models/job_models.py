from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


VALID_JOB_STATUSES = ("New", "Interesting", "Reviewed", "Skipped", "Applied")


class NormalizedUpworkJob(BaseModel):
    """Normalized job record stored by the research dashboard."""

    externalJobId: str | None = None
    jobUrl: str | None = None
    title: str
    description: str | None = None
    searchKeyword: str
    matchedKeywords: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    budgetType: str | None = None
    fixedBudget: float | None = None
    hourlyMin: float | None = None
    hourlyMax: float | None = None
    clientCountry: str | None = None
    clientSpent: str | None = None
    clientRating: float | None = None
    paymentVerified: bool | None = None
    proposalsCount: str | None = None
    postedAt: str | None = None
    scrapedAt: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    lastSeenAt: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    status: str = "New"
    rawJson: dict[str, Any] = Field(default_factory=dict)
    clientHires: str | None = None
    clientJobsPosted: str | None = None
    clientAvgHourlyRatePaid: str | None = None
    clientTotalReviews: str | None = None
    jobDuration: str | None = None
    experienceLevel: str | None = None
    connectsRequired: str | None = None
    category: str | None = None
    subcategory: str | None = None


class StoredUpworkJob(NormalizedUpworkJob):
    """Job record loaded from SQLite with database metadata."""

    id: int


class UpsertJobsSummary(BaseModel):
    """Summary of a database upsert operation."""

    totalJobsFetched: int
    newJobsAdded: int
    duplicatesFound: int
    insertedJobIds: list[int] = Field(default_factory=list)


class ScanRunSummary(BaseModel):
    """Summary shown after running the scraper."""

    totalJobsFetched: int
    newJobsAdded: int
    duplicatesFound: int
    errors: list[str] = Field(default_factory=list)
    rawItemsCount: int = 0
    normalizedItemsCount: int = 0
    insertedJobsCount: int = 0
    skippedJobsCount: int = 0
