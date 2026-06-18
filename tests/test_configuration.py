import json

import pytest

from src.core.config import loadApplicationSettings, loadConfiguredKeywords


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
    monkeypatch.delenv("APIFY_API_TOKEN", raising=False)

    loadedSettings = loadApplicationSettings()

    assert loadedSettings.apifyApiToken == ""
    assert loadedSettings.apifyActorId == "gio21/upwork-jobs-scraper"
    assert loadedSettings.resultsPerKeyword == 50
