from src.services.job_normalization_service import normalizeRawUpworkJob
from src.repositories.job_repository import JobRepository


def test_normalize_gio_actor_job_extracts_required_market_fields():
    rawJobPayload = {
        "jobId": "022027586354497239213",
        "title": "AI automation specialist",
        "description": "Build internal workflow automation.",
        "contractType": "Hourly: $60.00 - $120.00",
        "budget": "$60.00 - $120.00",
        "experienceLevel": "Expert",
        "duration": "More than 6 months",
        "postedOn": "13 hours ago",
        "extraSkills": ["Zapier", "n8n"],
        "proposals": "10 to 15",
        "clientCountry": "United States",
        "clientTotalSpent": "$50K+",
        "clientVerified": True,
        "url": "https://www.upwork.com/jobs/~022027586354497239213",
    }

    normalizedJob = normalizeRawUpworkJob(rawJobPayload, "AI automation")

    assert normalizedJob.externalJobId == "022027586354497239213"
    assert normalizedJob.jobUrl == "https://www.upwork.com/jobs/~022027586354497239213"
    assert normalizedJob.title == "AI automation specialist"
    assert normalizedJob.searchKeyword == "AI automation"
    assert normalizedJob.matchedKeywords == ["AI automation"]
    assert normalizedJob.budgetType == "hourly"
    assert normalizedJob.hourlyMin == 60
    assert normalizedJob.hourlyMax == 120
    assert normalizedJob.fixedBudget is None
    assert normalizedJob.skills == ["Zapier", "n8n"]
    assert normalizedJob.clientCountry == "United States"
    assert normalizedJob.clientSpent == "$50K+"
    assert normalizedJob.paymentVerified is True
    assert normalizedJob.proposalsCount == "10 to 15"


def test_normalize_neatrat_actor_job_preserves_raw_payload_and_fixed_budget():
    rawJobPayload = {
        "job_id": "abc123",
        "url": "https://www.upwork.com/jobs/~abc123",
        "title": "Dashboard automation",
        "description": "Need a reporting dashboard.",
        "type": "Fixed-price",
        "fixed_budget_amount": 2500,
        "skills": ["Business Intelligence"],
        "category_name": "Data Analytics",
        "ts_publish": "2026-06-18T09:00:00Z",
        "client": {"country": "Canada", "totalSpent": "$10K+"},
    }

    normalizedJob = normalizeRawUpworkJob(rawJobPayload, "dashboard automation")

    assert normalizedJob.externalJobId == "abc123"
    assert normalizedJob.budgetType == "fixed"
    assert normalizedJob.fixedBudget == 2500
    assert normalizedJob.hourlyMin is None
    assert normalizedJob.hourlyMax is None
    assert normalizedJob.category == "Data Analytics"
    assert normalizedJob.rawJson["job_id"] == "abc123"


def test_normalize_apify_numeric_client_fields_to_strings():
    rawJobPayload = {
        "jobId": "numeric-client-fields",
        "url": "https://www.upwork.com/jobs/~numeric-client-fields",
        "title": "AI workflow build",
        "description": "Build automations.",
        "client": {
            "countryCode": "US",
            "totalSpent": 767.19,
            "stats": {
                "totalHires": 4,
                "jobsPosted": 12,
                "avgHourlyRatePaid": 42.5,
                "totalReviews": 8,
            },
        },
    }

    normalizedJob = normalizeRawUpworkJob(rawJobPayload, "AI automation")

    assert normalizedJob.clientSpent == "767.19"
    assert normalizedJob.clientHires == "4"
    assert normalizedJob.clientJobsPosted == "12"
    assert normalizedJob.clientAvgHourlyRatePaid == "42.5"
    assert normalizedJob.clientTotalReviews == "8"


def test_normalize_apify_none_client_fields_remain_none():
    rawJobPayload = {
        "jobId": "none-client-fields",
        "title": "AI workflow build",
        "client": {
            "totalSpent": None,
            "stats": {
                "totalHires": None,
                "jobsPosted": None,
                "avgHourlyRatePaid": None,
                "totalReviews": None,
            },
        },
    }

    normalizedJob = normalizeRawUpworkJob(rawJobPayload, "AI automation")

    assert normalizedJob.clientSpent is None
    assert normalizedJob.clientHires is None
    assert normalizedJob.clientJobsPosted is None
    assert normalizedJob.clientAvgHourlyRatePaid is None
    assert normalizedJob.clientTotalReviews is None


def test_normalize_apify_string_client_fields_stay_strings():
    rawJobPayload = {
        "jobId": "string-client-fields",
        "title": "AI workflow build",
        "client": {
            "totalSpent": "$1K+",
            "stats": {
                "totalHires": "4",
                "jobsPosted": "12",
                "avgHourlyRatePaid": "$42.50",
                "totalReviews": "8",
            },
        },
    }

    normalizedJob = normalizeRawUpworkJob(rawJobPayload, "AI automation")

    assert normalizedJob.clientSpent == "$1K+"
    assert normalizedJob.clientHires == "4"
    assert normalizedJob.clientJobsPosted == "12"
    assert normalizedJob.clientAvgHourlyRatePaid == "$42.50"
    assert normalizedJob.clientTotalReviews == "8"


def test_normalized_numeric_client_fields_insert_into_sqlite(tmp_path):
    rawJobPayload = {
        "jobId": "sqlite-numeric-client-fields",
        "url": "https://www.upwork.com/jobs/~sqlite-numeric-client-fields",
        "title": "AI workflow build",
        "client": {"totalSpent": 767.19, "stats": {"totalHires": 4}},
    }
    normalizedJob = normalizeRawUpworkJob(rawJobPayload, "AI automation")
    jobRepository = JobRepository(tmp_path / "jobs.db")

    insertSummary = jobRepository.upsertNormalizedJobs([normalizedJob])
    storedJob = jobRepository.getJobById(insertSummary.insertedJobIds[0])

    assert insertSummary.newJobsAdded == 1
    assert storedJob.clientSpent == "767.19"
    assert storedJob.clientHires == "4"
