import re
from typing import Any

from src.models.job_models import NormalizedUpworkJob


MONEY_PATTERN = re.compile(r"[\d,.]+")


def normalizeRawUpworkJob(rawJobPayload: dict[str, Any], searchKeyword: str) -> NormalizedUpworkJob:
    """Normalize raw Upwork actor output into the storage model."""

    externalJobId = _firstString(rawJobPayload, ["jobId", "job_id", "id", "job_uid", "uid"])
    jobUrl = _firstString(rawJobPayload, ["url", "job_url", "link", "externalLink"])
    title = _firstString(rawJobPayload, ["title", "job_title"]) or "Untitled Upwork job"
    description = _firstString(rawJobPayload, ["description", "job_description"])
    contractType = _firstString(rawJobPayload, ["contractType", "type", "job_type"])
    fixedBudget = _firstNumber(rawJobPayload, ["fixed_budget_amount", "fixedBudget"])
    budgetText = _firstString(rawJobPayload, ["budget", "fixed_budget"])
    hourlyMin = _firstNumber(rawJobPayload, ["hourly_min", "hourlyMin"])
    hourlyMax = _firstNumber(rawJobPayload, ["hourly_max", "hourlyMax"])

    if hourlyMin is None or hourlyMax is None:
        parsedHourlyRange = _parseHourlyRange(contractType or budgetText or "")
        hourlyMin = hourlyMin if hourlyMin is not None else parsedHourlyRange[0]
        hourlyMax = hourlyMax if hourlyMax is not None else parsedHourlyRange[1]

    if fixedBudget is None and _looksLikeFixedBudget(contractType, budgetText):
        fixedBudget = _parseMoneyValue(budgetText or "")

    budgetType = _resolveBudgetType(contractType, fixedBudget, hourlyMin, hourlyMax)
    rawClientPayload = rawJobPayload.get("client") if isinstance(rawJobPayload.get("client"), dict) else {}

    return NormalizedUpworkJob(
        externalJobId=externalJobId,
        jobUrl=jobUrl,
        title=title,
        description=description,
        searchKeyword=searchKeyword,
        matchedKeywords=[searchKeyword],
        skills=_extractSkills(rawJobPayload),
        budgetType=budgetType,
        fixedBudget=fixedBudget,
        hourlyMin=hourlyMin,
        hourlyMax=hourlyMax,
        clientCountry=_firstString(rawJobPayload, ["clientCountry", "client_country"]) or rawClientPayload.get("country"),
        clientSpent=_firstString(rawJobPayload, ["clientTotalSpent", "client_spent"]) or rawClientPayload.get("totalSpent"),
        clientRating=_firstNumber(rawJobPayload, ["clientRating", "client_rating"]),
        paymentVerified=_firstBoolean(rawJobPayload, ["clientVerified", "payment_verified"]),
        proposalsCount=_firstString(rawJobPayload, ["proposals", "proposals_count", "applicants"]),
        postedAt=_firstString(rawJobPayload, ["postedOn", "posted_at", "ts_publish", "publishedAt"]),
        rawJson=rawJobPayload,
        clientHires=_firstString(rawJobPayload, ["clientHires", "client_hires"]),
        clientJobsPosted=_firstString(rawJobPayload, ["clientJobsPosted", "client_jobs_posted"]),
        clientAvgHourlyRatePaid=_firstString(rawJobPayload, ["clientAvgHourlyRatePaid"]),
        clientTotalReviews=_firstString(rawJobPayload, ["clientTotalReviews"]),
        jobDuration=_firstString(rawJobPayload, ["duration", "job_duration", "estimated_time"]),
        experienceLevel=_firstString(rawJobPayload, ["experienceLevel", "level", "experience_level"]),
        connectsRequired=_firstString(rawJobPayload, ["connectsRequired", "connects_required"]),
        category=_firstString(rawJobPayload, ["category", "category_name"]),
        subcategory=_firstString(rawJobPayload, ["subcategory", "subcategory_name"]),
    )


def _firstString(rawPayload: dict[str, Any], candidateKeys: list[str]) -> str | None:
    for candidateKey in candidateKeys:
        rawValue = rawPayload.get(candidateKey)
        if rawValue is not None and str(rawValue).strip():
            return str(rawValue).strip()
    return None


def _firstNumber(rawPayload: dict[str, Any], candidateKeys: list[str]) -> float | None:
    for candidateKey in candidateKeys:
        rawValue = rawPayload.get(candidateKey)
        parsedValue = _parseMoneyValue(rawValue)
        if parsedValue is not None:
            return parsedValue
    return None


def _firstBoolean(rawPayload: dict[str, Any], candidateKeys: list[str]) -> bool | None:
    for candidateKey in candidateKeys:
        rawValue = rawPayload.get(candidateKey)
        if isinstance(rawValue, bool):
            return rawValue
        if isinstance(rawValue, str) and rawValue.lower() in {"true", "false"}:
            return rawValue.lower() == "true"
    return None


def _extractSkills(rawPayload: dict[str, Any]) -> list[str]:
    rawSkills = rawPayload.get("extraSkills") or rawPayload.get("skills") or []
    if isinstance(rawSkills, str):
        return [skillValue.strip() for skillValue in rawSkills.split(",") if skillValue.strip()]
    if isinstance(rawSkills, list):
        return [str(skillValue).strip() for skillValue in rawSkills if str(skillValue).strip()]
    return []


def _parseHourlyRange(rawBudgetText: str) -> tuple[float | None, float | None]:
    parsedMoneyValues = [_parseMoneyValue(match.group()) for match in MONEY_PATTERN.finditer(rawBudgetText)]
    numericValues = [moneyValue for moneyValue in parsedMoneyValues if moneyValue is not None]
    if len(numericValues) >= 2:
        return numericValues[0], numericValues[1]
    if len(numericValues) == 1 and "hour" in rawBudgetText.lower():
        return numericValues[0], numericValues[0]
    return None, None


def _parseMoneyValue(rawValue: Any) -> float | None:
    if isinstance(rawValue, int | float):
        return float(rawValue)
    if not isinstance(rawValue, str):
        return None
    matchedMoneyValue = MONEY_PATTERN.search(rawValue.replace(",", ""))
    if not matchedMoneyValue:
        return None
    return float(matchedMoneyValue.group())


def _looksLikeFixedBudget(contractType: str | None, budgetText: str | None) -> bool:
    combinedBudgetText = f"{contractType or ''} {budgetText or ''}".lower()
    return "fixed" in combinedBudgetText and "hour" not in combinedBudgetText


def _resolveBudgetType(
    contractType: str | None,
    fixedBudget: float | None,
    hourlyMin: float | None,
    hourlyMax: float | None,
) -> str | None:
    contractTypeText = (contractType or "").lower()
    if "hour" in contractTypeText or hourlyMin is not None or hourlyMax is not None:
        return "hourly"
    if "fixed" in contractTypeText or fixedBudget is not None:
        return "fixed"
    return None
