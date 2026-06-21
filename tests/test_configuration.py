import json
from pathlib import Path

import pytest

from src.core.config import buildScanPlan, loadApplicationSettings, loadConfiguredKeywords, loadFileBackedApplicationSettings


CONFIG_ENVIRONMENT_KEYS = [
    "APIFY_API_TOKEN",
    "UPWORK_RESEARCH_SETTINGS_PATH",
    "UPWORK_RESEARCH_APIFY_ACTOR_ID",
    "UPWORK_RESEARCH_MAX_KEYWORDS_PER_SCAN",
    "UPWORK_RESEARCH_RESULTS_PER_KEYWORD",
    "UPWORK_RESEARCH_MAX_TOTAL_RESULTS_PER_SCAN",
    "UPWORK_RESEARCH_REQUEST_TIMEOUT_SECONDS",
    "UPWORK_RESEARCH_KEYWORDS_PATH",
    "UPWORK_RESEARCH_DATABASE_PATH",
    "UPWORK_RESEARCH_SESSION_SECRET",
    "UPWORK_RESEARCH_DASHBOARD_HOST",
    "UPWORK_RESEARCH_DASHBOARD_PORT",
    "UPWORK_RESEARCH_SCAN_CONCURRENCY_LIMIT",
    "UPWORK_RESEARCH_DRY_RUN",
    "ALLOW_LARGE_SCAN",
]


def clearConfigurationEnvironment(monkeypatch):
    for environmentKey in CONFIG_ENVIRONMENT_KEYS:
        monkeypatch.delenv(environmentKey, raising=False)


def test_load_configured_keywords_rejects_empty_keyword_file(tmp_path):
    keywordConfigPath = tmp_path / "keywords.json"
    keywordConfigPath.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="At least one keyword"):
        loadConfiguredKeywords(keywordConfigPath)


def test_load_configured_keywords_trims_and_deduplicates_keywords(tmp_path):
    keywordConfigPath = tmp_path / "keywords.json"
    keywordConfigPath.write_text(
        json.dumps([" AI automation ", "AI automation", "n8n"]),
        encoding="utf-8",
    )

    configuredKeywords = loadConfiguredKeywords(keywordConfigPath)

    assert configuredKeywords == ["AI automation", "n8n"]


def test_load_application_settings_requires_apify_token_for_live_scans(monkeypatch):
    clearConfigurationEnvironment(monkeypatch)
    monkeypatch.setattr("src.core.config.load_dotenv", lambda: None)
    monkeypatch.setenv("APIFY_API_TOKEN", "")

    loadedSettings = loadApplicationSettings()

    assert loadedSettings.apifyApiToken == ""
    assert loadedSettings.apifyActorId == "upwork-vibe/upwork-job-scraper"
    assert loadedSettings.maxKeywordsPerScan == 3
    assert loadedSettings.resultsPerKeyword == 10
    assert loadedSettings.maxTotalResultsPerScan == 30
    assert loadedSettings.scanConcurrencyLimit == 1
    assert loadedSettings.dryRun is True
    assert loadedSettings.dashboardHost == "127.0.0.1"
    assert loadedSettings.dashboardPort == 8000


def test_load_file_backed_application_settings_uses_settings_json_values(tmp_path, monkeypatch):
    clearConfigurationEnvironment(monkeypatch)
    settingsConfigPath = tmp_path / "settings.json"
    settingsConfigPath.write_text(
        json.dumps(
            {
                "apify_actor_id": "upwork-vibe/upwork-job-scraper",
                "max_keywords_per_scan": 5,
                "results_per_keyword": 25,
                "max_total_results_per_scan": 75,
                "request_timeout_seconds": 90,
                "keywords_path": "custom/keywords.json",
                "database_path": "custom/jobs.db",
                "session_secret": "local-secret",
                "dashboard_host": "127.0.0.1",
                "dashboard_port": 8765,
                "scan_concurrency_limit": 6,
                "dry_run": False,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("APIFY_API_TOKEN", "")

    loadedSettings = loadFileBackedApplicationSettings(settingsConfigPath)

    assert loadedSettings.apifyActorId == "upwork-vibe/upwork-job-scraper"
    assert loadedSettings.maxKeywordsPerScan == 5
    assert loadedSettings.resultsPerKeyword == 25
    assert loadedSettings.maxTotalResultsPerScan == 75
    assert loadedSettings.requestTimeoutSeconds == 90
    assert loadedSettings.keywordsPath.as_posix() == "custom/keywords.json"
    assert loadedSettings.databasePath.as_posix() == "custom/jobs.db"
    assert loadedSettings.sessionSecret == "local-secret"
    assert loadedSettings.dashboardHost == "127.0.0.1"
    assert loadedSettings.dashboardPort == 8765
    assert loadedSettings.scanConcurrencyLimit == 6
    assert loadedSettings.dryRun is False


def test_environment_variables_override_settings_json_values(tmp_path, monkeypatch):
    clearConfigurationEnvironment(monkeypatch)
    settingsConfigPath = tmp_path / "settings.json"
    settingsConfigPath.write_text(json.dumps({"results_per_keyword": 25}), encoding="utf-8")
    monkeypatch.setenv("UPWORK_RESEARCH_RESULTS_PER_KEYWORD", "75")

    loadedSettings = loadFileBackedApplicationSettings(settingsConfigPath)

    assert loadedSettings.resultsPerKeyword == 75


def test_load_application_settings_uses_configured_settings_path(tmp_path, monkeypatch):
    clearConfigurationEnvironment(monkeypatch)
    monkeypatch.setattr("src.core.config.load_dotenv", lambda: None)
    settingsConfigPath = tmp_path / "settings.json"
    settingsConfigPath.write_text(json.dumps({"dashboard_port": 8123}), encoding="utf-8")
    monkeypatch.setenv("UPWORK_RESEARCH_SETTINGS_PATH", str(settingsConfigPath))
    monkeypatch.delenv("UPWORK_RESEARCH_DASHBOARD_PORT", raising=False)

    loadedSettings = loadApplicationSettings()

    assert loadedSettings.dashboardPort == 8123


def test_build_scan_plan_uses_safe_defaults(monkeypatch):
    clearConfigurationEnvironment(monkeypatch)
    loadedSettings = loadFileBackedApplicationSettings(Path("missing.json"))

    scanPlan = buildScanPlan(["a", "b", "c", "d"], loadedSettings)

    assert scanPlan.keywords == ["a", "b", "c"]
    assert scanPlan.resultsPerKeyword == 10
    assert scanPlan.estimatedActorRuns == 3
    assert scanPlan.estimatedMaxRequestedJobs == 30
    assert scanPlan.scanConcurrencyLimit == 1
    assert scanPlan.dryRun is True


def test_build_scan_plan_clamps_high_values_without_large_scan_override(tmp_path, monkeypatch):
    clearConfigurationEnvironment(monkeypatch)
    settingsConfigPath = tmp_path / "settings.json"
    settingsConfigPath.write_text(
        json.dumps(
            {
                "max_keywords_per_scan": 99,
                "results_per_keyword": 99,
                "max_total_results_per_scan": 999,
                "scan_concurrency_limit": 99,
                "dry_run": True,
            }
        ),
        encoding="utf-8",
    )
    loadedSettings = loadFileBackedApplicationSettings(settingsConfigPath)

    scanPlan = buildScanPlan([str(index) for index in range(20)], loadedSettings)

    assert len(scanPlan.keywords) == 5
    assert scanPlan.resultsPerKeyword == 20
    assert scanPlan.estimatedMaxRequestedJobs == 100
    assert scanPlan.scanConcurrencyLimit == 2
    assert scanPlan.hardSafetyLimitExceeded is True
    assert any("max_keywords_per_scan clamped" in note for note in scanPlan.safetyNotes)
    assert any("results_per_keyword clamped" in note for note in scanPlan.safetyNotes)


def test_build_scan_plan_allows_large_values_with_override(tmp_path, monkeypatch):
    clearConfigurationEnvironment(monkeypatch)
    settingsConfigPath = tmp_path / "settings.json"
    settingsConfigPath.write_text(
        json.dumps(
            {
                "max_keywords_per_scan": 12,
                "results_per_keyword": 25,
                "max_total_results_per_scan": 300,
                "scan_concurrency_limit": 3,
                "dry_run": False,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("ALLOW_LARGE_SCAN", "true")
    loadedSettings = loadFileBackedApplicationSettings(settingsConfigPath)

    scanPlan = buildScanPlan([str(index) for index in range(20)], loadedSettings)

    assert len(scanPlan.keywords) == 12
    assert scanPlan.resultsPerKeyword == 25
    assert scanPlan.estimatedMaxRequestedJobs == 300
    assert scanPlan.scanConcurrencyLimit == 3
    assert scanPlan.allowLargeScan is True
    assert scanPlan.hardSafetyLimitExceeded is False
