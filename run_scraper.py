import asyncio

from src.core.config import loadApplicationSettings, loadConfiguredKeywords
from src.repositories.job_repository import JobRepository
from src.scrapers.apify_upwork_scraper import ApifyUpworkScraper
from src.services.scan_orchestration_service import UpworkScanOrchestrator


async def runConfiguredUpworkScan() -> None:
    """Run the configured Upwork scan from the command line."""

    applicationSettings = loadApplicationSettings()
    configuredKeywords = loadConfiguredKeywords(applicationSettings.keywordsPath)
    jobRepository = JobRepository(applicationSettings.databasePath)
    apifyUpworkScraper = ApifyUpworkScraper(
        applicationSettings.apifyApiToken,
        applicationSettings.apifyActorId,
        applicationSettings.requestTimeoutSeconds,
    )
    scanOrchestrator = UpworkScanOrchestrator(
        apifyUpworkScraper,
        jobRepository,
        applicationSettings.resultsPerKeyword,
    )
    scanSummary = await scanOrchestrator.runKeywordScan(configuredKeywords)

    print(f"Total fetched: {scanSummary.totalJobsFetched}")
    print(f"New jobs: {scanSummary.newJobsAdded}")
    print(f"Duplicates: {scanSummary.duplicatesFound}")
    if scanSummary.errors:
        print("Errors:")
        for scanError in scanSummary.errors:
            print(f"- {scanError}")


if __name__ == "__main__":
    asyncio.run(runConfiguredUpworkScan())
