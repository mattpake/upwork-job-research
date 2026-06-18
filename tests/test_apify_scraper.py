from src.scrapers.apify_upwork_scraper import ApifyUpworkScraper


class FakeApifyDatasetClient:
    def __init__(self, datasetItems):
        self.datasetItems = datasetItems

    def iterate_items(self):
        return iter(self.datasetItems)


class FakeApifyActorClient:
    def __init__(self):
        self.receivedRunInput = None

    def call(self, run_input):
        self.receivedRunInput = run_input
        return {"defaultDatasetId": "dataset-1"}


class FakeApifyClient:
    def __init__(self, datasetItems):
        self.datasetItems = datasetItems
        self.actorClient = FakeApifyActorClient()
        self.receivedActorId = None
        self.receivedDatasetId = None

    def actor(self, actorId):
        self.receivedActorId = actorId
        return self.actorClient

    def dataset(self, datasetId):
        self.receivedDatasetId = datasetId
        return FakeApifyDatasetClient(self.datasetItems)


def test_apify_scraper_builds_default_gio_actor_keyword_payload():
    apifyUpworkScraper = ApifyUpworkScraper("token", "gio21/upwork-jobs-scraper", 120)

    actorInputPayload = apifyUpworkScraper._buildActorInputPayload("AI automation", 25)

    assert actorInputPayload == {"query": "AI automation", "max_jobs": 25}


def test_apify_scraper_builds_neatrat_payload_from_local_api_docs():
    apifyUpworkScraper = ApifyUpworkScraper("token", "neatrat/upwork-job-scraper", 120)

    actorInputPayload = apifyUpworkScraper._buildActorInputPayload("web scraping", 50)

    assert actorInputPayload["query"] == "web scraping"
    assert actorInputPayload["page"] == 1
    assert actorInputPayload["pagesToScrape"] == 1
    assert actorInputPayload["perPage"] == 50
    assert actorInputPayload["sort"] == "newest"


def test_apify_scraper_builds_upwork_vibe_keyword_payload():
    apifyUpworkScraper = ApifyUpworkScraper("token", "upwork-vibe/upwork-job-scraper", 120)

    actorInputPayload = apifyUpworkScraper._buildActorInputPayload("n8n", 10)

    assert actorInputPayload["limit"] == 10
    assert actorInputPayload["rawUrl"] == ""
    assert actorInputPayload["fromDate"] == "2026-01-01"
    assert actorInputPayload["toDate"] == "2026-12-31"
    assert actorInputPayload["includeKeywords.keywords"] == ["n8n"]
    assert actorInputPayload["includeKeywords.matchTitle"] is True
    assert actorInputPayload["includeKeywords.matchDescription"] is True
    assert actorInputPayload["includeKeywords.matchSkills"] is True
    assert actorInputPayload["excludeKeywords.keywords"] == []
    assert actorInputPayload["budget.hourlyRate.min"] == "5"
    assert actorInputPayload["budget.fixedPrice.max"] == "10000"
    assert actorInputPayload["client.paymentMethodVerified"] is None
    assert actorInputPayload["addons.enableClientDetails"] is False
    assert actorInputPayload["notifications.shouldSendRunMetadata"] is True


def test_apify_scraper_uses_python_sdk_actor_and_dataset_clients():
    fakeApifyClient = FakeApifyClient([{"title": "AI automation job"}, "ignored item"])
    apifyUpworkScraper = ApifyUpworkScraper(
        "token",
        "upwork-vibe/upwork-job-scraper",
        120,
        apifyClientFactory=lambda apiToken: fakeApifyClient,
    )

    fetchedJobs = apifyUpworkScraper._fetchJobsForKeywordSynchronously("AI automation", 10)

    assert fakeApifyClient.receivedActorId == "upwork-vibe/upwork-job-scraper"
    assert fakeApifyClient.actorClient.receivedRunInput["includeKeywords.keywords"] == ["AI automation"]
    assert fakeApifyClient.receivedDatasetId == "dataset-1"
    assert fetchedJobs == [{"title": "AI automation job"}]
