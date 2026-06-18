import asyncio
import logging

from src.services.scan_orchestration_service import UpworkScanOrchestrator


class FakeFailingApifyScraper:
    async def fetchJobsForKeyword(self, keyword: str, maxJobs: int):
        raise RuntimeError(f"{keyword} failed")


class FakeEmptyJobRepository:
    def upsertNormalizedJobs(self, normalizedJobs):
        class FakeUpsertSummary:
            totalJobsFetched = len(normalizedJobs)
            newJobsAdded = 0
            duplicatesFound = 0

        return FakeUpsertSummary()


def test_scan_orchestrator_logs_keyword_errors(caplog):
    scanOrchestrator = UpworkScanOrchestrator(
        FakeFailingApifyScraper(),
        FakeEmptyJobRepository(),
        resultsPerKeyword=10,
        scanConcurrencyLimit=2,
    )

    with caplog.at_level(logging.INFO):
        scanSummary = asyncio.run(scanOrchestrator.runKeywordScan(["AI automation"]))

    assert scanSummary.errors == ["AI automation: AI automation failed"]
    assert "keyword_scan_failed" in caplog.text
    assert "scan_finished" in caplog.text
