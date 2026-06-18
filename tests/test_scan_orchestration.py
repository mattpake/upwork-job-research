import asyncio
import time

from src.models.job_models import NormalizedUpworkJob
from src.services.scan_orchestration_service import UpworkScanOrchestrator


class FakeSlowApifyScraper:
    async def fetchJobsForKeyword(self, keyword: str, maxJobs: int):
        await asyncio.sleep(0.05)
        return [{"jobId": keyword, "title": f"{keyword} job", "url": f"https://example.com/{keyword}"}]


class FakeJobRepository:
    def upsertNormalizedJobs(self, normalizedJobs: list[NormalizedUpworkJob]):
        class FakeUpsertSummary:
            totalJobsFetched = len(normalizedJobs)
            newJobsAdded = len(normalizedJobs)
            duplicatesFound = 0

        return FakeUpsertSummary()


def test_keyword_scan_runs_with_configured_concurrency_limit():
    scanOrchestrator = UpworkScanOrchestrator(
        FakeSlowApifyScraper(),
        FakeJobRepository(),
        resultsPerKeyword=10,
        scanConcurrencyLimit=4,
    )

    startedAt = time.perf_counter()
    scanSummary = asyncio.run(scanOrchestrator.runKeywordScan(["a", "b", "c", "d"]))
    elapsedSeconds = time.perf_counter() - startedAt

    assert elapsedSeconds < 0.12
    assert scanSummary.totalJobsFetched == 4
    assert scanSummary.newJobsAdded == 4
