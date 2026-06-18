import asyncio
import logging
from typing import Any


logger = logging.getLogger(__name__)


class ApifyScraperError(RuntimeError):
    """Raised when an Apify scraper run fails."""


class ApifyUpworkScraper:
    """Runs the configured Apify Upwork actor and returns raw dataset items."""

    def __init__(
        self,
        apiToken: str,
        actorId: str,
        timeoutSeconds: int,
        apifyClientFactory=None,
    ) -> None:
        self.apiToken = apiToken
        self.actorId = actorId
        self.timeoutSeconds = timeoutSeconds
        # If no factory provided, try to import the real ApifyClient now.
        if apifyClientFactory is None:
            try:
                from apify_client import ApifyClient as _ApifyClient

                apifyClientFactory = _ApifyClient
            except Exception:
                apifyClientFactory = None

        self.apifyClientFactory = apifyClientFactory

    async def fetchJobsForKeyword(self, keyword: str, maxJobs: int) -> list[dict[str, Any]]:
        """Run the configured Apify actor synchronously for one keyword."""

        if not self.apiToken:
            raise ApifyScraperError("APIFY_API_TOKEN is required before running a live Upwork scan.")

        return await asyncio.to_thread(self._fetchJobsForKeywordSynchronously, keyword, maxJobs)

    def _fetchJobsForKeywordSynchronously(self, keyword: str, maxJobs: int) -> list[dict[str, Any]]:
        """Run the Apify Python SDK call path for one keyword."""

        actorInputPayload = self._buildActorInputPayload(keyword, maxJobs)
        # Ensure `rawUrl` is always a string (Apify actor validation rejects nulls).
        if "rawUrl" in actorInputPayload and not isinstance(actorInputPayload["rawUrl"], str):
            actorInputPayload["rawUrl"] = ""
        # Some actor versions (e.g., upwork-vibe/upwork-job-scraper) reject the `rawUrl` property entirely.
        if self.actorId == "upwork-vibe/upwork-job-scraper" and "rawUrl" in actorInputPayload:
            del actorInputPayload["rawUrl"]
        # Remove any keys with None values to avoid API validation errors.
        keys_with_none = [k for k, v in actorInputPayload.items() if v is None]
        for k in keys_with_none:
            del actorInputPayload[k]
        logger.info("apify_sdk_run_started actor=%s keyword=%s max_jobs=%s", self.actorId, keyword, maxJobs)
        if not self.apifyClientFactory:
            raise ApifyScraperError("Apify client factory is not available (missing apify_client package).")

        apifyClient = self.apifyClientFactory(self.apiToken)
        actorRun = apifyClient.actor(self.actorId).call(run_input=actorInputPayload)
        # Actor client may return either a dict (older SDK) or an object (newer SDK).
        datasetId = None
        if isinstance(actorRun, dict):
            datasetId = actorRun.get("defaultDatasetId") or actorRun.get("default_dataset_id")
        else:
            datasetId = getattr(actorRun, "default_dataset_id", None) or getattr(actorRun, "defaultDatasetId", None)
        if not datasetId:
            raise ApifyScraperError("Apify actor run did not return a default dataset id.")

        datasetItems = list(apifyClient.dataset(datasetId).iterate_items())
        logger.info("apify_sdk_run_finished actor=%s keyword=%s items=%s", self.actorId, keyword, len(datasetItems))
        return [datasetItem for datasetItem in datasetItems if isinstance(datasetItem, dict)]

    def _buildActorInputPayload(self, keyword: str, maxJobs: int) -> dict[str, Any]:
        if self.actorId == "gio21/upwork-jobs-scraper":
            return {"query": keyword, "max_jobs": maxJobs}
        if self.actorId == "upwork-vibe/upwork-job-scraper":
            return {
                "limit": maxJobs,
                "searchPeriod": None,
                "rawUrl": "",
                "fromDate": "2026-01-01",
                "toDate": "2026-12-31",
                "jobCategories": [],
                "includeKeywords.keywords": [keyword],
                "includeKeywords.matchTitle": True,
                "includeKeywords.matchDescription": True,
                "includeKeywords.matchSkills": True,
                "excludeKeywords.keywords": [],
                "excludeKeywords.matchTitle": True,
                "excludeKeywords.matchDescription": True,
                "excludeKeywords.matchSkills": True,
                "budget.allowUnspecifiedBudget": True,
                "budget.hourlyRate.min": "5",
                "budget.hourlyRate.max": "150",
                "budget.avgHourlyRate.min": "5",
                "budget.avgHourlyRate.max": "150",
                "budget.fixedPrice.min": "50",
                "budget.fixedPrice.max": "10000",
                "budget.connectsPrice.min": 1,
                "budget.connectsPrice.max": 10,
                "budget.jobDurations": [
                    "UNSPECIFIED",
                    "UP_TO_ONE_MONTH",
                    "UP_TO_THREE_MONTHS",
                    "UP_TO_SIX_MONTHS",
                    "MORE_THAN_SIX_MONTHS",
                ],
                "budget.hourlyWorkloads": [
                    "UNSPECIFIED",
                    "LESS_THAN_30_HOURS",
                    "MORE_THAN_30_HOURS",
                ],
                "budget.noAvgHourlyRatePaid": False,
                "budget.noHireRate": False,
                "budget.onlyContractToHire": False,
                "budget.minClientHireRate": 0,
                "client.companySizeRange": [
                    "UNSPECIFIED",
                    "SOLO_ENTERPRENEUR",
                    "UP_TO_10_EMPLOYEES",
                    "UP_TO_100_EMPOLOYEES",
                    "UP_TO_500_EMPLOYEES",
                    "UP_TO_1K_EMPLOYEES",
                    "MORE_THAN_1K_EMPLOYEES",
                ],
                "client.descriptionLanguage.exclude": [],
                "client.descriptionLanguage.include": [],
                "client.hireHistory": ["NONE", "UP_TO", "MORE_THAN"],
                "client.includeLocations": None,
                "client.excludeLocations": None,
                "client.includeIndustry": None,
                "client.excludeIndustry": None,
                "client.includeWithNoFeedback": None,
                "client.totalSpent.min": None,
                "client.totalSpent.max": None,
                "client.minFeedbackScore": None,
                "client.paymentMethodVerified": None,
                "client.phoneNumberVerified": None,
                "client.timezones": None,
                "vendor.type": None,
                "vendor.languages": None,
                "vendor.englishProficiency": None,
                "vendor.experienceLevel": None,
                "vendor.minCustomJobScore": None,
                "vendor.includeLocations": None,
                "vendor.excludeLocations": None,
                "vendor.includeFeatured": None,
                "vendor.includeWithoutCountryPreference": None,
                "vendor.excludeWithQuestions": None,
                "jobIds": [],
                "addons.enableClientDetails": False,
                "addons.enableClientActivity": False,
                "addons.enableJobAttachments": False,
                "notifications.shouldSendRunMetadata": True,
                "notifications.limit": 3,
                "notifications.telegram.token": None,
                "notifications.telegram.channelId": None,
                "notifications.discord.token": None,
                "notifications.discord.channelId": None,
                "notifications.slack.token": None,
                "notifications.slack.channelId": None,
            }
        if self.actorId == "neatrat/upwork-job-scraper":
            return {
                "query": keyword,
                "rawUrl": "",
                "page": 1,
                "pagesToScrape": 1,
                "perPage": maxJobs,
                "sort": "newest",
            }

        return {"query": keyword, "max_jobs": maxJobs}
