import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_APIFY_ACTOR_ID = "upwork-vibe/upwork-job-scraper"
DEFAULT_RESULTS_PER_KEYWORD = 50
DEFAULT_KEYWORDS_PATH = Path("config/keywords.json")
DEFAULT_SETTINGS_PATH = Path("config/settings.json")
DEFAULT_DATABASE_PATH = Path("database/upwork_jobs.db")
DEFAULT_REQUEST_TIMEOUT_SECONDS = 120
DEFAULT_SESSION_SECRET = "local-upwork-research-dashboard-session"
DEFAULT_DASHBOARD_HOST = "127.0.0.1"
DEFAULT_DASHBOARD_PORT = 8000
DEFAULT_SCAN_CONCURRENCY_LIMIT = 4


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
    dashboardHost: str
    dashboardPort: int
    scanConcurrencyLimit: int


def loadApplicationSettings() -> ApplicationSettings:
    """Load application settings from settings JSON and environment variables."""

    load_dotenv()
    settingsConfigPath = Path(os.getenv("UPWORK_RESEARCH_SETTINGS_PATH", str(DEFAULT_SETTINGS_PATH)))
    return loadFileBackedApplicationSettings(settingsConfigPath)


def loadFileBackedApplicationSettings(settingsConfigPath: Path) -> ApplicationSettings:
    """Load application settings using settings JSON values with environment overrides."""

    fileSettings = _loadSettingsJson(settingsConfigPath)
    resultsPerKeyword = int(
        os.getenv(
            "UPWORK_RESEARCH_RESULTS_PER_KEYWORD",
            str(fileSettings.get("results_per_keyword", DEFAULT_RESULTS_PER_KEYWORD)),
        )
    )
    requestTimeoutSeconds = int(
        os.getenv(
            "UPWORK_RESEARCH_REQUEST_TIMEOUT_SECONDS",
            str(fileSettings.get("request_timeout_seconds", DEFAULT_REQUEST_TIMEOUT_SECONDS)),
        )
    )
    dashboardPort = int(
        os.getenv(
            "UPWORK_RESEARCH_DASHBOARD_PORT",
            str(fileSettings.get("dashboard_port", DEFAULT_DASHBOARD_PORT)),
        )
    )
    scanConcurrencyLimit = int(
        os.getenv(
            "UPWORK_RESEARCH_SCAN_CONCURRENCY_LIMIT",
            str(fileSettings.get("scan_concurrency_limit", DEFAULT_SCAN_CONCURRENCY_LIMIT)),
        )
    )

    return ApplicationSettings(
        apifyApiToken=os.getenv("APIFY_API_TOKEN", ""),
        apifyActorId=os.getenv(
            "UPWORK_RESEARCH_APIFY_ACTOR_ID",
            str(fileSettings.get("apify_actor_id", DEFAULT_APIFY_ACTOR_ID)),
        ),
        resultsPerKeyword=resultsPerKeyword,
        keywordsPath=Path(
            os.getenv("UPWORK_RESEARCH_KEYWORDS_PATH", str(fileSettings.get("keywords_path", DEFAULT_KEYWORDS_PATH)))
        ),
        databasePath=Path(
            os.getenv("UPWORK_RESEARCH_DATABASE_PATH", str(fileSettings.get("database_path", DEFAULT_DATABASE_PATH)))
        ),
        requestTimeoutSeconds=requestTimeoutSeconds,
        sessionSecret=os.getenv(
            "UPWORK_RESEARCH_SESSION_SECRET",
            str(fileSettings.get("session_secret", DEFAULT_SESSION_SECRET)),
        ),
        dashboardHost=os.getenv(
            "UPWORK_RESEARCH_DASHBOARD_HOST",
            str(fileSettings.get("dashboard_host", DEFAULT_DASHBOARD_HOST)),
        ),
        dashboardPort=dashboardPort,
        scanConcurrencyLimit=max(1, scanConcurrencyLimit),
    )


def _loadSettingsJson(settingsConfigPath: Path) -> dict[str, object]:
    if not settingsConfigPath.exists():
        return {}
    rawSettings = json.loads(settingsConfigPath.read_text(encoding="utf-8"))
    if not isinstance(rawSettings, dict):
        raise ValueError("Settings config must contain a JSON object.")
    return rawSettings


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
