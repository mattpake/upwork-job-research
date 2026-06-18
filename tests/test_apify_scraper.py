from src.scrapers.apify_upwork_scraper import ApifyUpworkScraper


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
    assert actorInputPayload["includeKeywords.keywords"] == ["n8n"]
    assert actorInputPayload["includeKeywords.matchDescription"] is True
