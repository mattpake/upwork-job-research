from typing import Any

import httpx


APIFY_API_BASE_URL = "https://api.apify.com/v2"


class ApifyScraperError(RuntimeError):
    """Raised when an Apify scraper run fails."""


class ApifyUpworkScraper:
    """Runs the configured Apify Upwork actor and returns raw dataset items."""

    def __init__(self, apiToken: str, actorId: str, timeoutSeconds: int) -> None:
        self.apiToken = apiToken
        self.actorId = actorId
        self.timeoutSeconds = timeoutSeconds

    async def fetchJobsForKeyword(self, keyword: str, maxJobs: int) -> list[dict[str, Any]]:
        """Run the configured Apify actor synchronously for one keyword."""

        if not self.apiToken:
            raise ApifyScraperError("APIFY_API_TOKEN is required before running a live Upwork scan.")

        actorPath = self.actorId.replace("/", "~")
        requestUrl = f"{APIFY_API_BASE_URL}/acts/{actorPath}/run-sync-get-dataset-items"
        actorInputPayload = self._buildActorInputPayload(keyword, maxJobs)

        async with httpx.AsyncClient(timeout=self.timeoutSeconds) as httpClient:
            apifyResponse = await httpClient.post(
                requestUrl,
                headers={"Authorization": f"Bearer {self.apiToken}"},
                json=actorInputPayload,
            )

        if apifyResponse.status_code >= 400:
            raise ApifyScraperError(f"Apify actor failed with HTTP {apifyResponse.status_code}: {apifyResponse.text}")

        responsePayload = apifyResponse.json()
        if not isinstance(responsePayload, list):
            raise ApifyScraperError("Apify actor response was not a dataset item array.")

        return [rawJobItem for rawJobItem in responsePayload if isinstance(rawJobItem, dict)]

    def _buildActorInputPayload(self, keyword: str, maxJobs: int) -> dict[str, Any]:
        if self.actorId == "gio21/upwork-jobs-scraper":
            return {"query": keyword, "max_jobs": maxJobs}
        if self.actorId == "upwork-vibe/upwork-job-scraper":
            return {
                "limit": maxJobs,
                "includeKeywords.keywords": [keyword],
                "includeKeywords.matchTitle": True,
                "includeKeywords.matchSkills": True,
                "includeKeywords.matchDescription": True,
            }
        if self.actorId == "neatrat/upwork-job-scraper":
            return {"query": keyword, "maxItems": maxJobs}

        return {"query": keyword, "max_jobs": maxJobs}
