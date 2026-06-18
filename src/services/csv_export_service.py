import csv
import io
import json

from src.models.job_models import StoredUpworkJob


CSV_EXPORT_FIELD_NAMES = [
    "id",
    "external_job_id",
    "job_url",
    "title",
    "description",
    "search_keyword",
    "matched_keywords",
    "skills",
    "budget_type",
    "fixed_budget",
    "hourly_min",
    "hourly_max",
    "client_country",
    "client_spent",
    "client_rating",
    "payment_verified",
    "proposals_count",
    "posted_at",
    "scraped_at",
    "last_seen_at",
    "status",
    "raw_json",
]


def buildJobsCsv(storedJobs: list[StoredUpworkJob]) -> str:
    """Build a CSV payload containing normalized fields for the provided jobs."""

    csvBuffer = io.StringIO()
    csvWriter = csv.DictWriter(csvBuffer, fieldnames=CSV_EXPORT_FIELD_NAMES, lineterminator="\n")
    csvWriter.writeheader()
    for storedJob in storedJobs:
        csvWriter.writerow(
            {
                "id": storedJob.id,
                "external_job_id": storedJob.externalJobId or "",
                "job_url": storedJob.jobUrl or "",
                "title": storedJob.title,
                "description": storedJob.description or "",
                "search_keyword": storedJob.searchKeyword,
                "matched_keywords": ", ".join(storedJob.matchedKeywords),
                "skills": ", ".join(storedJob.skills),
                "budget_type": storedJob.budgetType or "",
                "fixed_budget": storedJob.fixedBudget if storedJob.fixedBudget is not None else "",
                "hourly_min": storedJob.hourlyMin if storedJob.hourlyMin is not None else "",
                "hourly_max": storedJob.hourlyMax if storedJob.hourlyMax is not None else "",
                "client_country": storedJob.clientCountry or "",
                "client_spent": storedJob.clientSpent or "",
                "client_rating": storedJob.clientRating if storedJob.clientRating is not None else "",
                "payment_verified": storedJob.paymentVerified if storedJob.paymentVerified is not None else "",
                "proposals_count": storedJob.proposalsCount or "",
                "posted_at": storedJob.postedAt or "",
                "scraped_at": storedJob.scrapedAt,
                "last_seen_at": storedJob.lastSeenAt,
                "status": storedJob.status,
                "raw_json": json.dumps(storedJob.rawJson, ensure_ascii=True, separators=(",", ":")),
            }
        )
    return csvBuffer.getvalue()
