import asyncio
import logging

from src.models.job_models import NormalizedUpworkJob, ScanRunSummary
from src.repositories.job_repository import JobRepository
from src.scrapers.apify_upwork_scraper import ApifyUpworkScraper
from src.services.job_normalization_service import normalizeRawUpworkJob


logger = logging.getLogger(__name__)


class UpworkScanOrchestrator:
    """Coordinates keyword scans, normalization, and persistence."""

    def __init__(
        self,
        apifyUpworkScraper: ApifyUpworkScraper,
        jobRepository: JobRepository,
        resultsPerKeyword: int,
        scanConcurrencyLimit: int = 4,
    ) -> None:
        self.apifyUpworkScraper = apifyUpworkScraper
        self.jobRepository = jobRepository
        self.resultsPerKeyword = resultsPerKeyword
        self.scanConcurrencyLimit = scanConcurrencyLimit

    async def runKeywordScan(self, configuredKeywords: list[str]) -> ScanRunSummary:
        """Run the configured scraper for all keywords and store normalized jobs."""

        logger.info(
            "scan_started keywords=%s results_per_keyword=%s concurrency=%s",
            len(configuredKeywords),
            self.resultsPerKeyword,
            self.scanConcurrencyLimit,
        )
        normalizedJobs: list[NormalizedUpworkJob] = []
        scanErrors: list[str] = []
        keywordSemaphore = asyncio.Semaphore(self.scanConcurrencyLimit)

        async def fetchAndNormalizeKeyword(configuredKeyword: str) -> list[NormalizedUpworkJob]:
            async with keywordSemaphore:
                logger.info("keyword_scan_started keyword=%s", configuredKeyword)
                rawJobPayloads = await self.apifyUpworkScraper.fetchJobsForKeyword(
                    configuredKeyword,
                    self.resultsPerKeyword,
                )
                logger.info("keyword_scan_finished keyword=%s fetched=%s", configuredKeyword, len(rawJobPayloads))
                return [normalizeRawUpworkJob(rawJobPayload, configuredKeyword) for rawJobPayload in rawJobPayloads]

        keywordScanResults = await asyncio.gather(
            *(fetchAndNormalizeKeyword(configuredKeyword) for configuredKeyword in configuredKeywords),
            return_exceptions=True,
        )

        for configuredKeyword, keywordScanResult in zip(configuredKeywords, keywordScanResults, strict=True):
            if isinstance(keywordScanResult, Exception):
                logger.exception("keyword_scan_failed keyword=%s", configuredKeyword, exc_info=keywordScanResult)
                scanErrors.append(f"{configuredKeyword}: {keywordScanResult}")
                continue
            normalizedJobs.extend(keywordScanResult)

        upsertSummary = self.jobRepository.upsertNormalizedJobs(normalizedJobs)
        logger.info(
            "scan_finished fetched=%s new=%s duplicates=%s errors=%s",
            upsertSummary.totalJobsFetched,
            upsertSummary.newJobsAdded,
            upsertSummary.duplicatesFound,
            len(scanErrors),
        )
        return ScanRunSummary(
            totalJobsFetched=upsertSummary.totalJobsFetched,
            newJobsAdded=upsertSummary.newJobsAdded,
            duplicatesFound=upsertSummary.duplicatesFound,
            errors=scanErrors,
        )
