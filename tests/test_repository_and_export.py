import csv
import io

from src.models.job_models import NormalizedUpworkJob
from src.repositories.job_repository import JobRepository
from src.services.csv_export_service import buildJobsCsv


def buildSampleJob(keyword: str, externalJobId: str = "job-1") -> NormalizedUpworkJob:
    return NormalizedUpworkJob(
        externalJobId=externalJobId,
        jobUrl=f"https://www.upwork.com/jobs/~{externalJobId}",
        title="AI workflow automation",
        description="Automate sales operations.",
        searchKeyword=keyword,
        matchedKeywords=[keyword],
        skills=["Zapier"],
        budgetType="fixed",
        fixedBudget=1200,
        hourlyMin=None,
        hourlyMax=None,
        clientCountry="United States",
        clientSpent="$10K+",
        clientRating=None,
        paymentVerified=True,
        proposalsCount="Less than 5",
        postedAt="2026-06-18T09:00:00Z",
        status="New",
        rawJson={"jobId": externalJobId},
    )


def test_job_repository_deduplicates_jobs_and_merges_matched_keywords(tmp_path):
    databasePath = tmp_path / "upwork_jobs.db"
    jobRepository = JobRepository(databasePath)
    jobRepository.initializeDatabase()

    firstInsertSummary = jobRepository.upsertNormalizedJobs([buildSampleJob("AI automation")])
    duplicateInsertSummary = jobRepository.upsertNormalizedJobs([buildSampleJob("n8n")])
    storedJobs = jobRepository.listJobs()

    assert firstInsertSummary.newJobsAdded == 1
    assert duplicateInsertSummary.duplicatesFound == 1
    assert len(storedJobs) == 1
    assert storedJobs[0].matchedKeywords == ["AI automation", "n8n"]
    assert storedJobs[0].searchKeyword == "AI automation"


def test_build_jobs_csv_includes_all_normalized_fields(tmp_path):
    databasePath = tmp_path / "upwork_jobs.db"
    jobRepository = JobRepository(databasePath)
    jobRepository.initializeDatabase()
    jobRepository.upsertNormalizedJobs([buildSampleJob("AI automation")])

    csvPayload = buildJobsCsv(jobRepository.listJobs())
    csvRows = list(csv.DictReader(io.StringIO(csvPayload)))

    assert csvRows[0]["external_job_id"] == "job-1"
    assert csvRows[0]["matched_keywords"] == "AI automation"
    assert csvRows[0]["fixed_budget"] == "1200.0"
    assert csvRows[0]["raw_json"] == '{"jobId":"job-1"}'
