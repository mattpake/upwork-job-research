from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from src.core.config import loadApplicationSettings, loadConfiguredKeywords
from src.models.job_models import VALID_JOB_STATUSES
from src.repositories.job_repository import JobRepository
from src.scrapers.apify_upwork_scraper import ApifyUpworkScraper
from src.services.csv_export_service import buildJobsCsv
from src.services.scan_orchestration_service import UpworkScanOrchestrator


templates = Jinja2Templates(directory="src/web/templates")
dashboardRouter = APIRouter()


@dashboardRouter.get("/", response_class=HTMLResponse)
async def renderDashboard(
    request: Request,
    keyword: str = "",
    status: str = "",
    budget_type: str = "",
    client_country: str = "",
    payment_verified: str = "",
    text_search: str = "",
    minimum_fixed_budget: str = "",
    minimum_hourly_rate: str = "",
    maximum_hourly_rate: str = "",
    scraped_after: str = "",
    posted_after: str = "",
) -> HTMLResponse:
    applicationSettings = loadApplicationSettings()
    configuredKeywords = loadConfiguredKeywords(applicationSettings.keywordsPath)
    jobRepository = JobRepository(applicationSettings.databasePath)
    activeFilters = _buildActiveFilters(
        keyword,
        status,
        budget_type,
        client_country,
        payment_verified,
        text_search,
        minimum_fixed_budget,
        minimum_hourly_rate,
        maximum_hourly_rate,
        scraped_after,
        posted_after,
    )
    storedJobs = jobRepository.listJobs(activeFilters)
    selectedJob = storedJobs[0] if storedJobs else None
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "configuredKeywords": configuredKeywords,
            "storedJobs": storedJobs,
            "selectedJob": selectedJob,
            "activeFilters": activeFilters,
            "validJobStatuses": VALID_JOB_STATUSES,
            "scanSummary": request.session.pop("scanSummary", None) if hasattr(request, "session") else None,
            "scanError": request.session.pop("scanError", None) if hasattr(request, "session") else None,
        },
    )


@dashboardRouter.post("/scan")
async def runUpworkScan(request: Request) -> RedirectResponse:
    applicationSettings = loadApplicationSettings()
    configuredKeywords = loadConfiguredKeywords(applicationSettings.keywordsPath)
    jobRepository = JobRepository(applicationSettings.databasePath)
    apifyUpworkScraper = ApifyUpworkScraper(
        applicationSettings.apifyApiToken,
        applicationSettings.apifyActorId,
        applicationSettings.requestTimeoutSeconds,
    )
    scanOrchestrator = UpworkScanOrchestrator(
        apifyUpworkScraper,
        jobRepository,
        applicationSettings.resultsPerKeyword,
        applicationSettings.scanConcurrencyLimit,
    )
    scanSummary = await scanOrchestrator.runKeywordScan(configuredKeywords)
    if hasattr(request, "session"):
        request.session["scanSummary"] = scanSummary.model_dump()
    return RedirectResponse("/", status_code=303)


@dashboardRouter.post("/jobs/{job_id}/status")
async def updateJobStatus(job_id: int, status: str = Form(...)) -> RedirectResponse:
    if status not in VALID_JOB_STATUSES:
        raise ValueError(f"Unsupported job status: {status}")
    applicationSettings = loadApplicationSettings()
    JobRepository(applicationSettings.databasePath).updateJobStatus(job_id, status)
    return RedirectResponse("/", status_code=303)


@dashboardRouter.get("/export.csv")
async def exportJobsCsv(
    keyword: str = Query(""),
    status: str = Query(""),
    budget_type: str = Query(""),
    client_country: str = Query(""),
    payment_verified: str = Query(""),
    text_search: str = Query(""),
    minimum_fixed_budget: str = Query(""),
    minimum_hourly_rate: str = Query(""),
    maximum_hourly_rate: str = Query(""),
    scraped_after: str = Query(""),
    posted_after: str = Query(""),
) -> Response:
    applicationSettings = loadApplicationSettings()
    activeFilters = _buildActiveFilters(
        keyword,
        status,
        budget_type,
        client_country,
        payment_verified,
        text_search,
        minimum_fixed_budget,
        minimum_hourly_rate,
        maximum_hourly_rate,
        scraped_after,
        posted_after,
    )
    storedJobs = JobRepository(applicationSettings.databasePath).listJobs(activeFilters)
    return Response(
        content=buildJobsCsv(storedJobs),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="upwork-jobs.csv"'},
    )


def _buildActiveFilters(*rawFilterValues: str) -> dict[str, str]:
    filterKeys = [
        "keyword",
        "status",
        "budget_type",
        "client_country",
        "payment_verified",
        "text_search",
        "minimum_fixed_budget",
        "minimum_hourly_rate",
        "maximum_hourly_rate",
        "scraped_after",
        "posted_after",
    ]
    return {
        filterKey: rawFilterValue.strip()
        for filterKey, rawFilterValue in zip(filterKeys, rawFilterValues, strict=True)
        if rawFilterValue and rawFilterValue.strip()
    }
