import json

import pytest

from src.core.config import loadApplicationSettings, loadConfiguredKeywords, loadFileBackedApplicationSettings


CONFIG_ENVIRONMENT_KEYS = [
    "APIFY_API_TOKEN",
    "UPWORK_RESEARCH_SETTINGS_PATH",
    "UPWORK_RESEARCH_APIFY_ACTOR_ID",
    "UPWORK_RESEARCH_RESULTS_PER_KEYWORD",
    "UPWORK_RESEARCH_REQUEST_TIMEOUT_SECONDS",
    "UPWORK_RESEARCH_KEYWORDS_PATH",
    "UPWORK_RESEARCH_DATABASE_PATH",
    "UPWORK_RESEARCH_SESSION_SECRET",
    "UPWORK_RESEARCH_DASHBOARD_HOST",
    "UPWORK_RESEARCH_DASHBOARD_PORT",
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
    assert loadedSettings.apifyActorId == "neatrat/upwork-job-scraper"
    assert loadedSettings.resultsPerKeyword == 50
    assert loadedSettings.dashboardHost == "127.0.0.1"
    assert loadedSettings.dashboardPort == 8000


def test_load_file_backed_application_settings_uses_settings_json_values(tmp_path, monkeypatch):
    clearConfigurationEnvironment(monkeypatch)
    settingsConfigPath = tmp_path / "settings.json"
    settingsConfigPath.write_text(
        json.dumps(
            {
                "apify_actor_id": "neatrat/upwork-job-scraper",
                "results_per_keyword": 25,
                "request_timeout_seconds": 90,
                "keywords_path": "custom/keywords.json",
                "database_path": "custom/jobs.db",
                "session_secret": "local-secret",
                "dashboard_host": "127.0.0.1",
                "dashboard_port": 8765,
                "scan_concurrency_limit": 6,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("APIFY_API_TOKEN", "")

    loadedSettings = loadFileBackedApplicationSettings(settingsConfigPath)

    assert loadedSettings.apifyActorId == "neatrat/upwork-job-scraper"
    assert loadedSettings.resultsPerKeyword == 25
    assert loadedSettings.requestTimeoutSeconds == 90
    assert loadedSettings.keywordsPath.as_posix() == "custom/keywords.json"
    assert loadedSettings.databasePath.as_posix() == "custom/jobs.db"
    assert loadedSettings.sessionSecret == "local-secret"
    assert loadedSettings.dashboardHost == "127.0.0.1"
    assert loadedSettings.dashboardPort == 8765
    assert loadedSettings.scanConcurrencyLimit == 6


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
