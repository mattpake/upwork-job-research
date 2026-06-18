from src.models.job_models import NormalizedUpworkJob, ScanRunSummary
from src.repositories.job_repository import JobRepository
from src.scrapers.apify_upwork_scraper import ApifyUpworkScraper
from src.services.job_normalization_service import normalizeRawUpworkJob


class UpworkScanOrchestrator:
    """Coordinates keyword scans, normalization, and persistence."""

    def __init__(
        self,
        apifyUpworkScraper: ApifyUpworkScraper,
        jobRepository: JobRepository,
        resultsPerKeyword: int,
    ) -> None:
        self.apifyUpworkScraper = apifyUpworkScraper
        self.jobRepository = jobRepository
        self.resultsPerKeyword = resultsPerKeyword

    async def runKeywordScan(self, configuredKeywords: list[str]) -> ScanRunSummary:
        """Run the configured scraper for all keywords and store normalized jobs."""

        normalizedJobs: list[NormalizedUpworkJob] = []
        scanErrors: list[str] = []
        for configuredKeyword in configuredKeywords:
            try:
                rawJobPayloads = await self.apifyUpworkScraper.fetchJobsForKeyword(
                    configuredKeyword,
                    self.resultsPerKeyword,
                )
                normalizedJobs.extend(
                    normalizeRawUpworkJob(rawJobPayload, configuredKeyword) for rawJobPayload in rawJobPayloads
                )
            except Exception as scanError:
                scanErrors.append(f"{configuredKeyword}: {scanError}")

        upsertSummary = self.jobRepository.upsertNormalizedJobs(normalizedJobs)
        return ScanRunSummary(
            totalJobsFetched=upsertSummary.totalJobsFetched,
            newJobsAdded=upsertSummary.newJobsAdded,
            duplicatesFound=upsertSummary.duplicatesFound,
            errors=scanErrors,
        )
