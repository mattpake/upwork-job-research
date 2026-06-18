import json
import sqlite3

from src.models.job_models import StoredUpworkJob


def convertJobRowToStoredJob(jobRow: sqlite3.Row) -> StoredUpworkJob:
    """Convert a SQLite row into a typed stored job model."""

    return StoredUpworkJob(
        id=jobRow["id"],
        externalJobId=jobRow["external_job_id"],
        jobUrl=jobRow["job_url"],
        title=jobRow["title"],
        description=jobRow["description"],
        searchKeyword=jobRow["search_keyword"],
        matchedKeywords=json.loads(jobRow["matched_keywords"]),
        skills=json.loads(jobRow["skills"]),
        budgetType=jobRow["budget_type"],
        fixedBudget=jobRow["fixed_budget"],
        hourlyMin=jobRow["hourly_min"],
        hourlyMax=jobRow["hourly_max"],
        clientCountry=jobRow["client_country"],
        clientSpent=jobRow["client_spent"],
        clientRating=jobRow["client_rating"],
        paymentVerified=bool(jobRow["payment_verified"]) if jobRow["payment_verified"] is not None else None,
        proposalsCount=jobRow["proposals_count"],
        postedAt=jobRow["posted_at"],
        scrapedAt=jobRow["scraped_at"],
        lastSeenAt=jobRow["last_seen_at"],
        status=jobRow["status"],
        rawJson=json.loads(jobRow["raw_json"]),
        clientHires=jobRow["client_hires"],
        clientJobsPosted=jobRow["client_jobs_posted"],
        clientAvgHourlyRatePaid=jobRow["client_avg_hourly_rate_paid"],
        clientTotalReviews=jobRow["client_total_reviews"],
        jobDuration=jobRow["job_duration"],
        experienceLevel=jobRow["experience_level"],
        connectsRequired=jobRow["connects_required"],
        category=jobRow["category"],
        subcategory=jobRow["subcategory"],
    )
