from typing import Any


def appendJobFilterClauses(
    queryClauses: list[str],
    queryParameters: list[Any],
    activeFilters: dict[str, Any],
) -> None:
    """Append SQL where clauses for dashboard filters."""

    if activeFilters.get("keyword"):
        queryClauses.append("matched_keywords LIKE ?")
        queryParameters.append(f"%{activeFilters['keyword']}%")
    if activeFilters.get("status"):
        queryClauses.append("status = ?")
        queryParameters.append(activeFilters["status"])
    if activeFilters.get("budget_type"):
        queryClauses.append("budget_type = ?")
        queryParameters.append(activeFilters["budget_type"])
    if activeFilters.get("client_country"):
        queryClauses.append("client_country LIKE ?")
        queryParameters.append(f"%{activeFilters['client_country']}%")
    if activeFilters.get("payment_verified") in {"true", "false"}:
        queryClauses.append("payment_verified = ?")
        queryParameters.append(1 if activeFilters["payment_verified"] == "true" else 0)
    if activeFilters.get("text_search"):
        queryClauses.append("(title LIKE ? OR description LIKE ?)")
        queryParameters.extend([f"%{activeFilters['text_search']}%", f"%{activeFilters['text_search']}%"])
    if activeFilters.get("minimum_fixed_budget"):
        queryClauses.append("fixed_budget >= ?")
        queryParameters.append(float(activeFilters["minimum_fixed_budget"]))
    if activeFilters.get("minimum_hourly_rate"):
        queryClauses.append("hourly_max >= ?")
        queryParameters.append(float(activeFilters["minimum_hourly_rate"]))
    if activeFilters.get("maximum_hourly_rate"):
        queryClauses.append("hourly_min <= ?")
        queryParameters.append(float(activeFilters["maximum_hourly_rate"]))
    if activeFilters.get("scraped_after"):
        queryClauses.append("scraped_at >= ?")
        queryParameters.append(activeFilters["scraped_after"])
    if activeFilters.get("posted_after"):
        queryClauses.append("posted_at >= ?")
        queryParameters.append(activeFilters["posted_after"])
