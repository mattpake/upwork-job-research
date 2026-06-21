import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_APIFY_ACTOR_ID = "upwork-vibe/upwork-job-scraper"
DEFAULT_MAX_KEYWORDS_PER_SCAN = 3
DEFAULT_RESULTS_PER_KEYWORD = 10
DEFAULT_MAX_TOTAL_RESULTS_PER_SCAN = 30
DEFAULT_KEYWORDS_PATH = Path("config/keywords.json")
DEFAULT_SETTINGS_PATH = Path("config/settings.json")
DEFAULT_DATABASE_PATH = Path("database/upwork_jobs.db")
DEFAULT_REQUEST_TIMEOUT_SECONDS = 120
DEFAULT_SESSION_SECRET = "local-upwork-research-dashboard-session"
DEFAULT_DASHBOARD_HOST = "127.0.0.1"
DEFAULT_DASHBOARD_PORT = 8000
DEFAULT_SCAN_CONCURRENCY_LIMIT = 1
DEFAULT_DRY_RUN = True

HARD_MAX_KEYWORDS_PER_SCAN = 10
HARD_MAX_RESULTS_PER_KEYWORD = 20
HARD_MAX_TOTAL_RESULTS_PER_SCAN = 100
HARD_MAX_SCAN_CONCURRENCY_LIMIT = 2


@dataclass(frozen=True)
class ApplicationSettings:
    """Runtime settings loaded from environment variables."""

    apifyApiToken: str
    apifyActorId: str
    maxKeywordsPerScan: int
    resultsPerKeyword: int
    maxTotalResultsPerScan: int
    keywordsPath: Path
    databasePath: Path
    requestTimeoutSeconds: int
    sessionSecret: str
    dashboardHost: str
    dashboardPort: int
    scanConcurrencyLimit: int
    dryRun: bool
    allowLargeScan: bool


@dataclass(frozen=True)
class ScanPlan:
    """Effective safety-limited scan settings for one run."""

    keywords: list[str]
    requestedKeywordCount: int
    maxKeywordsPerScan: int
    resultsPerKeyword: int
    maxTotalResultsPerScan: int
    estimatedActorRuns: int
    estimatedMaxRequestedJobs: int
    scanConcurrencyLimit: int
    dryRun: bool
    allowLargeScan: bool
    hardSafetyLimitExceeded: bool
    safetyNotes: list[str]


def loadApplicationSettings() -> ApplicationSettings:
    """Load application settings from settings JSON and environment variables."""

    load_dotenv()
    settingsConfigPath = Path(os.getenv("UPWORK_RESEARCH_SETTINGS_PATH", str(DEFAULT_SETTINGS_PATH)))
    return loadFileBackedApplicationSettings(settingsConfigPath)


def loadFileBackedApplicationSettings(settingsConfigPath: Path) -> ApplicationSettings:
    """Load application settings using settings JSON values with environment overrides."""

    fileSettings = _loadSettingsJson(settingsConfigPath)
    maxKeywordsPerScan = int(
        os.getenv(
            "UPWORK_RESEARCH_MAX_KEYWORDS_PER_SCAN",
            str(fileSettings.get("max_keywords_per_scan", DEFAULT_MAX_KEYWORDS_PER_SCAN)),
        )
    )
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
    maxTotalResultsPerScan = int(
        os.getenv(
            "UPWORK_RESEARCH_MAX_TOTAL_RESULTS_PER_SCAN",
            str(fileSettings.get("max_total_results_per_scan", DEFAULT_MAX_TOTAL_RESULTS_PER_SCAN)),
        )
    )
    dryRun = _readBooleanSetting("UPWORK_RESEARCH_DRY_RUN", fileSettings.get("dry_run", DEFAULT_DRY_RUN))

    return ApplicationSettings(
        apifyApiToken=os.getenv("APIFY_API_TOKEN", ""),
        apifyActorId=os.getenv(
            "UPWORK_RESEARCH_APIFY_ACTOR_ID",
            str(fileSettings.get("apify_actor_id", DEFAULT_APIFY_ACTOR_ID)),
        ),
        maxKeywordsPerScan=max(1, maxKeywordsPerScan),
        resultsPerKeyword=max(1, resultsPerKeyword),
        maxTotalResultsPerScan=max(1, maxTotalResultsPerScan),
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
        dryRun=dryRun,
        allowLargeScan=_parseBoolean(os.getenv("ALLOW_LARGE_SCAN", "false")),
    )


def buildScanPlan(configuredKeywords: list[str], applicationSettings: ApplicationSettings) -> ScanPlan:
    """Build the effective scan plan, applying hard safety clamps unless explicitly disabled."""

    safetyNotes: list[str] = []
    effectiveMaxKeywords = applicationSettings.maxKeywordsPerScan
    effectiveResultsPerKeyword = applicationSettings.resultsPerKeyword
    effectiveMaxTotalResults = applicationSettings.maxTotalResultsPerScan
    effectiveConcurrency = applicationSettings.scanConcurrencyLimit
    hardSafetyLimitExceeded = False

    if not applicationSettings.allowLargeScan:
        hardSafetyLimitExceeded = (
            effectiveMaxKeywords > HARD_MAX_KEYWORDS_PER_SCAN
            or effectiveResultsPerKeyword > HARD_MAX_RESULTS_PER_KEYWORD
            or effectiveMaxTotalResults > HARD_MAX_TOTAL_RESULTS_PER_SCAN
            or effectiveConcurrency > HARD_MAX_SCAN_CONCURRENCY_LIMIT
        )
        effectiveMaxKeywords = _clampWithNote(
            effectiveMaxKeywords,
            HARD_MAX_KEYWORDS_PER_SCAN,
            "max_keywords_per_scan",
            safetyNotes,
        )
        effectiveResultsPerKeyword = _clampWithNote(
            effectiveResultsPerKeyword,
            HARD_MAX_RESULTS_PER_KEYWORD,
            "results_per_keyword",
            safetyNotes,
        )
        effectiveMaxTotalResults = _clampWithNote(
            effectiveMaxTotalResults,
            HARD_MAX_TOTAL_RESULTS_PER_SCAN,
            "max_total_results_per_scan",
            safetyNotes,
        )
        effectiveConcurrency = _clampWithNote(
            effectiveConcurrency,
            HARD_MAX_SCAN_CONCURRENCY_LIMIT,
            "scan_concurrency_limit",
            safetyNotes,
        )

    selectedKeywordLimit = min(len(configuredKeywords), effectiveMaxKeywords)
    if selectedKeywordLimit < len(configuredKeywords):
        safetyNotes.append(
            f"keywords truncated from {len(configuredKeywords)} to {selectedKeywordLimit}"
        )

    if effectiveResultsPerKeyword > effectiveMaxTotalResults:
        safetyNotes.append(
            f"results_per_keyword reduced from {effectiveResultsPerKeyword} to {effectiveMaxTotalResults} to fit max_total_results_per_scan"
        )
        effectiveResultsPerKeyword = effectiveMaxTotalResults

    maxKeywordsAllowedByTotal = max(1, effectiveMaxTotalResults // effectiveResultsPerKeyword)
    if selectedKeywordLimit > maxKeywordsAllowedByTotal:
        safetyNotes.append(
            f"keywords truncated from {selectedKeywordLimit} to {maxKeywordsAllowedByTotal} to fit max_total_results_per_scan"
        )
        selectedKeywordLimit = maxKeywordsAllowedByTotal

    selectedKeywords = configuredKeywords[:selectedKeywordLimit]
    estimatedMaxRequestedJobs = len(selectedKeywords) * effectiveResultsPerKeyword

    return ScanPlan(
        keywords=selectedKeywords,
        requestedKeywordCount=len(configuredKeywords),
        maxKeywordsPerScan=effectiveMaxKeywords,
        resultsPerKeyword=effectiveResultsPerKeyword,
        maxTotalResultsPerScan=effectiveMaxTotalResults,
        estimatedActorRuns=len(selectedKeywords),
        estimatedMaxRequestedJobs=estimatedMaxRequestedJobs,
        scanConcurrencyLimit=effectiveConcurrency,
        dryRun=applicationSettings.dryRun,
        allowLargeScan=applicationSettings.allowLargeScan,
        hardSafetyLimitExceeded=hardSafetyLimitExceeded,
        safetyNotes=safetyNotes,
    )


def _loadSettingsJson(settingsConfigPath: Path) -> dict[str, object]:
    if not settingsConfigPath.exists():
        return {}
    rawSettings = json.loads(settingsConfigPath.read_text(encoding="utf-8"))
    if not isinstance(rawSettings, dict):
        raise ValueError("Settings config must contain a JSON object.")
    return rawSettings


def _clampWithNote(value: int, hardLimit: int, settingName: str, safetyNotes: list[str]) -> int:
    if value <= hardLimit:
        return value
    safetyNotes.append(f"{settingName} clamped from {value} to {hardLimit}")
    return hardLimit


def _readBooleanSetting(environmentKey: str, fileValue: object) -> bool:
    environmentValue = os.getenv(environmentKey)
    if environmentValue is not None:
        return _parseBoolean(environmentValue)
    if isinstance(fileValue, bool):
        return fileValue
    return _parseBoolean(str(fileValue))


def _parseBoolean(rawValue: str) -> bool:
    return rawValue.strip().casefold() in {"1", "true", "yes", "on"}


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
