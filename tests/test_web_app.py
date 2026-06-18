from fastapi.testclient import TestClient

from src.web.application import createApplication


def test_dashboard_home_renders_run_scan_action(tmp_path, monkeypatch):
    monkeypatch.setenv("UPWORK_RESEARCH_DATABASE_PATH", str(tmp_path / "jobs.db"))
    monkeypatch.setenv("UPWORK_RESEARCH_KEYWORDS_PATH", str(tmp_path / "keywords.json"))
    (tmp_path / "keywords.json").write_text('["AI automation"]', encoding="utf-8")

    testClient = TestClient(createApplication())
    response = testClient.get("/")

    assert response.status_code == 200
    assert "Run Upwork Scan" in response.text
    assert "AI automation" in response.text
    assert "font-awesome" in response.text
    assert "data-scan-overlay" in response.text
    assert "Running Upwork scan" in response.text


def test_status_endpoint_updates_existing_job_status(tmp_path, monkeypatch):
    from src.models.job_models import NormalizedUpworkJob
    from src.repositories.job_repository import JobRepository

    databasePath = tmp_path / "jobs.db"
    monkeypatch.setenv("UPWORK_RESEARCH_DATABASE_PATH", str(databasePath))
    monkeypatch.setenv("UPWORK_RESEARCH_KEYWORDS_PATH", str(tmp_path / "keywords.json"))
    (tmp_path / "keywords.json").write_text('["AI automation"]', encoding="utf-8")

    jobRepository = JobRepository(databasePath)
    jobRepository.initializeDatabase()
    insertSummary = jobRepository.upsertNormalizedJobs(
        [
            NormalizedUpworkJob(
                externalJobId="job-1",
                jobUrl="https://www.upwork.com/jobs/~job-1",
                title="AI workflow automation",
                description="Automate sales operations.",
                searchKeyword="AI automation",
                matchedKeywords=["AI automation"],
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
                rawJson={"jobId": "job-1"},
            )
        ]
    )

    testClient = TestClient(createApplication())
    response = testClient.post(
        f"/jobs/{insertSummary.insertedJobIds[0]}/status",
        data={"status": "Interesting"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert JobRepository(databasePath).getJobById(insertSummary.insertedJobIds[0]).status == "Interesting"
