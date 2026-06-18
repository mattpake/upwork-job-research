import json
from typing import Any

from src.models.job_models import NormalizedUpworkJob


INSERT_JOB_SQL = """
INSERT INTO jobs (
    external_job_id, job_url, title, description, search_keyword, matched_keywords,
    skills, budget_type, fixed_budget, hourly_min, hourly_max, client_country,
    client_spent, client_rating, payment_verified, proposals_count, posted_at,
    scraped_at, last_seen_at, status, raw_json, client_hires, client_jobs_posted,
    client_avg_hourly_rate_paid, client_total_reviews, job_duration, experience_level,
    connects_required, category, subcategory
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def buildJobInsertParameters(normalizedJob: NormalizedUpworkJob) -> tuple[Any, ...]:
    """Build SQLite insert parameters for a normalized job."""

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
