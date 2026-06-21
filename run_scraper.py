import asyncio
import argparse
import logging

from src.core.config import buildScanPlan, loadApplicationSettings, loadConfiguredKeywords
from src.repositories.job_repository import JobRepository
from src.scrapers.apify_upwork_scraper import ApifyUpworkScraper
from src.services.scan_orchestration_service import UpworkScanOrchestrator


async def runConfiguredUpworkScan(forceLiveScan: bool = False) -> None:
    """Run the configured Upwork scan from the command line."""

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    applicationSettings = loadApplicationSettings()
    configuredKeywords = loadConfiguredKeywords(applicationSettings.keywordsPath)
    scanPlan = buildScanPlan(configuredKeywords, applicationSettings)
    dryRun = scanPlan.dryRun and not forceLiveScan

    print("Planned Upwork scan:")
    print(f"- Keywords configured: {scanPlan.requestedKeywordCount}")
    print(f"- Keywords to scan: {scanPlan.estimatedActorRuns}")
    print(f"- Results per keyword: {scanPlan.resultsPerKeyword}")
    print(f"- Max requested jobs: {scanPlan.estimatedMaxRequestedJobs}")
    print(f"- Concurrency: {scanPlan.scanConcurrencyLimit}")
    print(f"- Dry run: {dryRun}")
    if scanPlan.safetyNotes:
        print("Safety notes:")
        for safetyNote in scanPlan.safetyNotes:
            print(f"- {safetyNote}")

    if dryRun:
        print("Dry run enabled. No Apify calls were made.")
        return
    if scanPlan.hardSafetyLimitExceeded and not scanPlan.allowLargeScan:
        print("Live scan rejected because one or more settings exceed the hard safety limits.")
        print("Lower the scan limits or set ALLOW_LARGE_SCAN=true after confirming the cost.")
        return

    jobRepository = JobRepository(applicationSettings.databasePath)
    apifyUpworkScraper = ApifyUpworkScraper(
        applicationSettings.apifyApiToken,
        applicationSettings.apifyActorId,
        applicationSettings.requestTimeoutSeconds,
    )
    scanOrchestrator = UpworkScanOrchestrator(
        apifyUpworkScraper,
        jobRepository,
        scanPlan.resultsPerKeyword,
        scanPlan.scanConcurrencyLimit,
    )
    scanSummary = await scanOrchestrator.runKeywordScan(scanPlan.keywords)

    print(f"Total fetched: {scanSummary.totalJobsFetched}")
    print(f"New jobs: {scanSummary.newJobsAdded}")
    print(f"Duplicates: {scanSummary.duplicatesFound}")
    if scanSummary.errors:
        print("Errors:")
        for scanError in scanSummary.errors:
            print(f"- {scanError}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a safety-limited Upwork Apify scan.")
    parser.add_argument("--live", action="store_true", help="Allow a real Apify scan when dry_run is true.")
    parsedArguments = parser.parse_args()
    asyncio.run(runConfiguredUpworkScan(forceLiveScan=parsedArguments.live))
