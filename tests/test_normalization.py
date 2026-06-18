from src.services.job_normalization_service import normalizeRawUpworkJob


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
