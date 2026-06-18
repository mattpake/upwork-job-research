import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_APIFY_ACTOR_ID = "gio21/upwork-jobs-scraper"
DEFAULT_RESULTS_PER_KEYWORD = 50
DEFAULT_KEYWORDS_PATH = Path("config/keywords.json")
DEFAULT_DATABASE_PATH = Path("database/upwork_jobs.db")
DEFAULT_REQUEST_TIMEOUT_SECONDS = 120
DEFAULT_SESSION_SECRET = "local-upwork-research-dashboard-session"


@dataclass(frozen=True)
class ApplicationSettings:
    """Runtime settings loaded from environment variables."""

    apifyApiToken: str
    apifyActorId: str
    resultsPerKeyword: int
    keywordsPath: Path
    databasePath: Path
    requestTimeoutSeconds: int
    sessionSecret: str


def loadApplicationSettings() -> ApplicationSettings:
    """Load application settings from environment variables."""

    load_dotenv()
    resultsPerKeyword = int(os.getenv("UPWORK_RESEARCH_RESULTS_PER_KEYWORD", str(DEFAULT_RESULTS_PER_KEYWORD)))
    requestTimeoutSeconds = int(
        os.getenv("UPWORK_RESEARCH_REQUEST_TIMEOUT_SECONDS", str(DEFAULT_REQUEST_TIMEOUT_SECONDS))
    )

    return ApplicationSettings(
        apifyApiToken=os.getenv("APIFY_API_TOKEN", ""),
        apifyActorId=os.getenv("UPWORK_RESEARCH_APIFY_ACTOR_ID", DEFAULT_APIFY_ACTOR_ID),
        resultsPerKeyword=resultsPerKeyword,
        keywordsPath=Path(os.getenv("UPWORK_RESEARCH_KEYWORDS_PATH", str(DEFAULT_KEYWORDS_PATH))),
        databasePath=Path(os.getenv("UPWORK_RESEARCH_DATABASE_PATH", str(DEFAULT_DATABASE_PATH))),
        requestTimeoutSeconds=requestTimeoutSeconds,
        sessionSecret=os.getenv("UPWORK_RESEARCH_SESSION_SECRET", DEFAULT_SESSION_SECRET),
    )


def loadConfiguredKeywords(keywordConfigPath: Path) -> list[str]:
    """Load, trim, and deduplicate configured keyword strings."""

    if not keywordConfigPath.exists():
        raise FileNotFoundError(f"Keyword config file was not found: {keywordConfigPath}")

    rawKeywordValues = json.loads(keywordConfigPath.read_text(encoding="utf-8"))
    if not isinstance(rawKeywordValues, list):
        raise ValueError("Keyword config must contain a JSON array of strings.")

    configuredKeywords: list[str] = []
    seenKeywordKeys: set[str] = set()
    for rawKeywordValue in rawKeywordValues:
        if not isinstance(rawKeywordValue, str):
            raise ValueError("Every configured keyword must be a string.")
        normalizedKeyword = rawKeywordValue.strip()
        keywordKey = normalizedKeyword.casefold()
        if normalizedKeyword and keywordKey not in seenKeywordKeys:
            configuredKeywords.append(normalizedKeyword)
            seenKeywordKeys.add(keywordKey)

    if not configuredKeywords:
        raise ValueError("At least one keyword must be configured.")

    return configuredKeywords
