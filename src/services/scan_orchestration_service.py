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
        scanConcurrencyLimit: int = 1,
        dryRun: bool = False,
    ) -> None:
        self.apifyUpworkScraper = apifyUpworkScraper
        self.jobRepository = jobRepository
        self.resultsPerKeyword = resultsPerKeyword
        self.scanConcurrencyLimit = scanConcurrencyLimit
        self.dryRun = dryRun

    async def runKeywordScan(self, configuredKeywords: list[str]) -> ScanRunSummary:
        """Run the configured scraper for all keywords and store normalized jobs."""

        estimatedMaxRequestedJobs = len(configuredKeywords) * self.resultsPerKeyword
        logger.info(
            "scan_plan keywords=%s actor_runs=%s results_per_keyword=%s max_requested_jobs=%s concurrency=%s dry_run=%s",
            len(configuredKeywords),
            len(configuredKeywords),
            self.resultsPerKeyword,
            estimatedMaxRequestedJobs,
            self.scanConcurrencyLimit,
            self.dryRun,
        )
        if self.dryRun:
            logger.info("scan_dry_run_skipped_apify_calls")
            return ScanRunSummary(
                totalJobsFetched=0,
                newJobsAdded=0,
                duplicatesFound=0,
                errors=[],
                rawItemsCount=0,
                normalizedItemsCount=0,
                insertedJobsCount=0,
                skippedJobsCount=0,
            )

        logger.info(
            "scan_started keywords=%s results_per_keyword=%s concurrency=%s",
            len(configuredKeywords),
            self.resultsPerKeyword,
            self.scanConcurrencyLimit,
        )
        normalizedJobs: list[NormalizedUpworkJob] = []
        scanErrors: list[str] = []
        rawItemsCount = 0
        skippedJobsCount = 0
        keywordSemaphore = asyncio.Semaphore(self.scanConcurrencyLimit)

        async def fetchAndNormalizeKeyword(configuredKeyword: str) -> tuple[list[NormalizedUpworkJob], int, int]:
            async with keywordSemaphore:
                logger.info("keyword_scan_started keyword=%s", configuredKeyword)
                rawJobPayloads = await self.apifyUpworkScraper.fetchJobsForKeyword(
                    configuredKeyword,
                    self.resultsPerKeyword,
                )
                logger.info("keyword_scan_finished keyword=%s raw_items=%s", configuredKeyword, len(rawJobPayloads))
                keywordJobs: list[NormalizedUpworkJob] = []
                skippedKeywordJobs = 0
                for rawJobPayload in rawJobPayloads:
                    try:
                        keywordJobs.append(normalizeRawUpworkJob(rawJobPayload, configuredKeyword))
                    except Exception:
                        skippedKeywordJobs += 1
                        logger.exception("job_normalization_failed keyword=%s", configuredKeyword)
                logger.info(
                    "keyword_normalization_finished keyword=%s raw_items=%s normalized=%s skipped=%s",
                    configuredKeyword,
                    len(rawJobPayloads),
                    len(keywordJobs),
                    skippedKeywordJobs,
                )
                return keywordJobs, len(rawJobPayloads), skippedKeywordJobs

        keywordScanResults = await asyncio.gather(
            *(fetchAndNormalizeKeyword(configuredKeyword) for configuredKeyword in configuredKeywords),
            return_exceptions=True,
        )

        for configuredKeyword, keywordScanResult in zip(configuredKeywords, keywordScanResults, strict=True):
            if isinstance(keywordScanResult, Exception):
                logger.exception("keyword_scan_failed keyword=%s", configuredKeyword, exc_info=keywordScanResult)
                scanErrors.append(f"{configuredKeyword}: {keywordScanResult}")
                continue
            keywordJobs, keywordRawItemsCount, keywordSkippedJobsCount = keywordScanResult
            rawItemsCount += keywordRawItemsCount
            skippedJobsCount += keywordSkippedJobsCount
            normalizedJobs.extend(keywordJobs)

        upsertSummary = self.jobRepository.upsertNormalizedJobs(normalizedJobs)
        logger.info(
            "scan_finished raw_items=%s normalized=%s inserted=%s skipped=%s duplicates=%s errors=%s",
            rawItemsCount,
            len(normalizedJobs),
            upsertSummary.newJobsAdded,
            skippedJobsCount,
            upsertSummary.duplicatesFound,
            len(scanErrors),
        )
        return ScanRunSummary(
            totalJobsFetched=upsertSummary.totalJobsFetched,
            newJobsAdded=upsertSummary.newJobsAdded,
            duplicatesFound=upsertSummary.duplicatesFound,
            errors=scanErrors,
            rawItemsCount=rawItemsCount,
            normalizedItemsCount=len(normalizedJobs),
            insertedJobsCount=upsertSummary.newJobsAdded,
            skippedJobsCount=skippedJobsCount,
        )
