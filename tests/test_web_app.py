from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from src.services.scan_status_service import scanStatusRegistry
from src.web.application import createApplication


class FakeApifyScraper:
    def __init__(self, apiToken, actorId, timeoutSeconds):
        self.apiToken = apiToken
        self.actorId = actorId
        self.timeoutSeconds = timeoutSeconds

    async def fetchJobsForKeyword(self, keyword: str, maxJobs: int):
        return [
            {
                "jobId": f"{keyword}-job",
                "url": f"https://www.upwork.com/jobs/~{keyword}-job",
                "title": f"{keyword} job",
                "description": "Build an automation.",
                "client": {"totalSpent": 767.19, "stats": {"totalHires": 4}},
            }
        ]


def extractScanIdFromRedirect(response) -> str:
    location = response.headers["location"]
    parsedLocation = urlparse(location)
    return parse_qs(parsedLocation.query)["scan_id"][0]


def test_dashboard_home_renders_run_scan_action(tmp_path, monkeypatch):
    scanStatusRegistry.clear()
    monkeypatch.setenv("UPWORK_RESEARCH_DATABASE_PATH", str(tmp_path / "jobs.db"))
    monkeypatch.setenv("UPWORK_RESEARCH_KEYWORDS_PATH", str(tmp_path / "keywords.json"))
    monkeypatch.setenv("UPWORK_RESEARCH_MAX_KEYWORDS_PER_SCAN", "3")
    monkeypatch.setenv("UPWORK_RESEARCH_RESULTS_PER_KEYWORD", "10")
    monkeypatch.setenv("UPWORK_RESEARCH_MAX_TOTAL_RESULTS_PER_SCAN", "30")
    monkeypatch.setenv("UPWORK_RESEARCH_SCAN_CONCURRENCY_LIMIT", "1")
    monkeypatch.setenv("UPWORK_RESEARCH_DRY_RUN", "true")
    (tmp_path / "keywords.json").write_text('["AI automation"]', encoding="utf-8")

    testClient = TestClient(createApplication())
    response = testClient.get("/")

    assert response.status_code == 200
    assert "Preview Scan" in response.text
    assert "This scan will run 1 keywords, 10 results per keyword, max 10 jobs total." in response.text
    assert "Dry run on" in response.text
    assert "AI automation" in response.text
    assert "font-awesome" in response.text
    assert "data-scan-overlay" in response.text
    assert "Running Upwork scan" in response.text
    assert "Market research console" not in response.text
    assert '<i class="fa-brands fa-upwork" aria-hidden="true"></i>' not in response.text
    assert 'data-scan-summary="none"' in response.text
    assert 'data-active-scan-id=""' in response.text
    assert "Research Queue" in response.text
    assert "research-table" in response.text


def test_status_endpoint_updates_existing_job_status(tmp_path, monkeypatch):
    scanStatusRegistry.clear()
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


def test_dashboard_scan_respects_dry_run_without_calling_apify(tmp_path, monkeypatch):
    scanStatusRegistry.clear()
    monkeypatch.setenv("UPWORK_RESEARCH_DATABASE_PATH", str(tmp_path / "jobs.db"))
    monkeypatch.setenv("UPWORK_RESEARCH_KEYWORDS_PATH", str(tmp_path / "keywords.json"))
    monkeypatch.setenv("UPWORK_RESEARCH_MAX_KEYWORDS_PER_SCAN", "3")
    monkeypatch.setenv("UPWORK_RESEARCH_RESULTS_PER_KEYWORD", "10")
    monkeypatch.setenv("UPWORK_RESEARCH_MAX_TOTAL_RESULTS_PER_SCAN", "30")
    monkeypatch.setenv("UPWORK_RESEARCH_SCAN_CONCURRENCY_LIMIT", "1")
    monkeypatch.setenv("UPWORK_RESEARCH_DRY_RUN", "true")
    (tmp_path / "keywords.json").write_text('["AI automation", "n8n"]', encoding="utf-8")

    def failIfApifyIsCalled(*args, **kwargs):
        raise AssertionError("Apify scraper should not be created during dashboard dry run")

    monkeypatch.setattr("src.web.dashboard_routes.ApifyUpworkScraper", failIfApifyIsCalled)

    testClient = TestClient(createApplication())
    response = testClient.post("/scan", follow_redirects=False)
    scanId = extractScanIdFromRedirect(response)
    statusResponse = testClient.get(f"/scan/status/{scanId}")

    assert response.status_code == 303
    assert statusResponse.json()["status"] == "dry_run"
    assert statusResponse.json()["raw_items_count"] == 0


def test_dashboard_rejects_live_scan_above_hard_safety_limits(tmp_path, monkeypatch):
    scanStatusRegistry.clear()
    monkeypatch.setenv("UPWORK_RESEARCH_DATABASE_PATH", str(tmp_path / "jobs.db"))
    monkeypatch.setenv("UPWORK_RESEARCH_KEYWORDS_PATH", str(tmp_path / "keywords.json"))
    monkeypatch.setenv("UPWORK_RESEARCH_MAX_KEYWORDS_PER_SCAN", "99")
    monkeypatch.setenv("UPWORK_RESEARCH_RESULTS_PER_KEYWORD", "99")
    monkeypatch.setenv("UPWORK_RESEARCH_MAX_TOTAL_RESULTS_PER_SCAN", "999")
    monkeypatch.setenv("UPWORK_RESEARCH_SCAN_CONCURRENCY_LIMIT", "99")
    monkeypatch.setenv("UPWORK_RESEARCH_DRY_RUN", "false")
    monkeypatch.setenv("ALLOW_LARGE_SCAN", "false")
    (tmp_path / "keywords.json").write_text('["AI automation", "n8n"]', encoding="utf-8")

    def failIfApifyIsCalled(*args, **kwargs):
        raise AssertionError("Apify scraper should not be created for rejected scans")

    monkeypatch.setattr("src.web.dashboard_routes.ApifyUpworkScraper", failIfApifyIsCalled)

    testClient = TestClient(createApplication())
    response = testClient.post("/scan", follow_redirects=False)
    scanId = extractScanIdFromRedirect(response)
    statusResponse = testClient.get(f"/scan/status/{scanId}")

    assert response.status_code == 303
    assert statusResponse.json()["status"] == "failed"
    assert "hard safety limits" in statusResponse.json()["error_message"]


def test_dashboard_scan_redirects_with_scan_id_and_starts_running(tmp_path, monkeypatch):
    scanStatusRegistry.clear()
    monkeypatch.setenv("UPWORK_RESEARCH_DATABASE_PATH", str(tmp_path / "jobs.db"))
    monkeypatch.setenv("UPWORK_RESEARCH_KEYWORDS_PATH", str(tmp_path / "keywords.json"))
    monkeypatch.setenv("UPWORK_RESEARCH_MAX_KEYWORDS_PER_SCAN", "1")
    monkeypatch.setenv("UPWORK_RESEARCH_RESULTS_PER_KEYWORD", "1")
    monkeypatch.setenv("UPWORK_RESEARCH_MAX_TOTAL_RESULTS_PER_SCAN", "1")
    monkeypatch.setenv("UPWORK_RESEARCH_SCAN_CONCURRENCY_LIMIT", "1")
    monkeypatch.setenv("UPWORK_RESEARCH_DRY_RUN", "false")
    (tmp_path / "keywords.json").write_text('["AI automation"]', encoding="utf-8")

    async def leaveScanRunning(scanId: str):
        return None

    monkeypatch.setattr("src.web.dashboard_routes._runBackgroundScan", leaveScanRunning)

    testClient = TestClient(createApplication())
    response = testClient.post("/scan", follow_redirects=False)
    scanId = extractScanIdFromRedirect(response)
    statusResponse = testClient.get(f"/scan/status/{scanId}")

    assert response.status_code == 303
    assert response.headers["location"] == f"/?scan_id={scanId}"
    assert statusResponse.json()["status"] == "running"


def test_successful_background_scan_becomes_succeeded(tmp_path, monkeypatch):
    scanStatusRegistry.clear()
    monkeypatch.setenv("APIFY_API_TOKEN", "test-token")
    monkeypatch.setenv("UPWORK_RESEARCH_DATABASE_PATH", str(tmp_path / "jobs.db"))
    monkeypatch.setenv("UPWORK_RESEARCH_KEYWORDS_PATH", str(tmp_path / "keywords.json"))
    monkeypatch.setenv("UPWORK_RESEARCH_MAX_KEYWORDS_PER_SCAN", "1")
    monkeypatch.setenv("UPWORK_RESEARCH_RESULTS_PER_KEYWORD", "1")
    monkeypatch.setenv("UPWORK_RESEARCH_MAX_TOTAL_RESULTS_PER_SCAN", "1")
    monkeypatch.setenv("UPWORK_RESEARCH_SCAN_CONCURRENCY_LIMIT", "1")
    monkeypatch.setenv("UPWORK_RESEARCH_DRY_RUN", "false")
    (tmp_path / "keywords.json").write_text('["AI automation"]', encoding="utf-8")
    monkeypatch.setattr("src.web.dashboard_routes.ApifyUpworkScraper", FakeApifyScraper)

    testClient = TestClient(createApplication())
    response = testClient.post("/scan", follow_redirects=False)
    scanId = extractScanIdFromRedirect(response)
    statusPayload = testClient.get(f"/scan/status/{scanId}").json()

    assert response.status_code == 303
    assert statusPayload["status"] == "succeeded"
    assert statusPayload["raw_items_count"] == 1
    assert statusPayload["normalized_items_count"] == 1
    assert statusPayload["inserted_jobs_count"] == 1
    assert statusPayload["skipped_jobs_count"] == 0


def test_dashboard_exposes_scan_id_for_completion_polling(tmp_path, monkeypatch):
    scanStatusRegistry.clear()
    monkeypatch.setenv("UPWORK_RESEARCH_DATABASE_PATH", str(tmp_path / "jobs.db"))
    monkeypatch.setenv("UPWORK_RESEARCH_KEYWORDS_PATH", str(tmp_path / "keywords.json"))
    monkeypatch.setenv("UPWORK_RESEARCH_DRY_RUN", "true")
    (tmp_path / "keywords.json").write_text('["AI automation"]', encoding="utf-8")

    testClient = TestClient(createApplication())
    postResponse = testClient.post("/scan", follow_redirects=False)
    scanId = extractScanIdFromRedirect(postResponse)
    dashboardResponse = testClient.get(f"/?scan_id={scanId}")

    assert dashboardResponse.status_code == 200
    assert f'data-active-scan-id="{scanId}"' in dashboardResponse.text
    assert "data-scan-status-panel" in dashboardResponse.text
