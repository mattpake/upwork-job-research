import logging

from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from src.core.config import buildScanPlan, loadApplicationSettings, loadConfiguredKeywords
from src.models.job_models import VALID_JOB_STATUSES
from src.repositories.job_repository import JobRepository
from src.scrapers.apify_upwork_scraper import ApifyUpworkScraper
from src.services.csv_export_service import buildJobsCsv
from src.services.scan_orchestration_service import UpworkScanOrchestrator
from src.services.scan_status_service import scanStatusRegistry


templates = Jinja2Templates(directory="src/web/templates")
dashboardRouter = APIRouter()
logger = logging.getLogger(__name__)


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
    scan_id: str = "",
) -> HTMLResponse:
    applicationSettings = loadApplicationSettings()
    configuredKeywords = loadConfiguredKeywords(applicationSettings.keywordsPath)
    scanPlan = buildScanPlan(configuredKeywords, applicationSettings)
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
    scanSummary = request.session.pop("scanSummary", None) if hasattr(request, "session") else None
    scanState = "none"
    if scanSummary:
        scanState = "error" if scanSummary.get("errors") else "success"
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
            "scanPlan": scanPlan,
            "activeScanId": scan_id,
            "scanSummary": scanSummary,
            "scanState": scanState,
            "scanError": request.session.pop("scanError", None) if hasattr(request, "session") else None,
        },
    )


async def _runBackgroundScan(scanId: str) -> None:
    applicationSettings = loadApplicationSettings()
    configuredKeywords = loadConfiguredKeywords(applicationSettings.keywordsPath)
    scanPlan = buildScanPlan(configuredKeywords, applicationSettings)
    if scanPlan.dryRun:
        logger.info("dashboard_background_scan_skipped_dry_run")
        scanStatusRegistry.markDryRun(scanId)
        return

    scanStatusRegistry.markRunning(scanId)
    jobRepository = JobRepository(applicationSettings.databasePath)
    apifyUpworkScraper = ApifyUpworkScraper(
        applicationSettings.apifyApiToken,
        applicationSettings.apifyActorId,
        applicationSettings.requestTimeoutSeconds,
    )
    scanOrchestrator = UpworkScanOrchestrator(
        apifyUpworkScraper,
        jobRepository,
        scanPlan.resultsPerKeyword,
        scanPlan.scanConcurrencyLimit,
    )
    try:
        scanSummary = await scanOrchestrator.runKeywordScan(scanPlan.keywords)
        scanStatusRegistry.markSucceeded(scanId, scanSummary)
        logger.info(
            "dashboard_background_scan_succeeded scan_id=%s raw_items=%s normalized=%s inserted=%s skipped=%s",
            scanId,
            scanSummary.rawItemsCount,
            scanSummary.normalizedItemsCount,
            scanSummary.insertedJobsCount,
            scanSummary.skippedJobsCount,
        )
    except Exception as scanException:
        logger.exception("background_scan_failed")
        scanStatusRegistry.markFailed(scanId, str(scanException))


@dashboardRouter.post("/scan")
async def runUpworkScan(request: Request, background_tasks: BackgroundTasks) -> RedirectResponse:
    applicationSettings = loadApplicationSettings()
    configuredKeywords = loadConfiguredKeywords(applicationSettings.keywordsPath)
    scanPlan = buildScanPlan(configuredKeywords, applicationSettings)
    logger.info(
        "dashboard_scan_requested keywords=%s actor_runs=%s actor=%s results_per_keyword=%s max_requested_jobs=%s dry_run=%s",
        scanPlan.requestedKeywordCount,
        scanPlan.estimatedActorRuns,
        applicationSettings.apifyActorId,
        scanPlan.resultsPerKeyword,
        scanPlan.estimatedMaxRequestedJobs,
        scanPlan.dryRun,
    )
    scanState = scanStatusRegistry.createScan(scanPlan, status="running")

    if scanPlan.dryRun:
        scanStatusRegistry.markDryRun(scanState.scan_id)
        return RedirectResponse(f"/?scan_id={scanState.scan_id}", status_code=303)
    if scanPlan.hardSafetyLimitExceeded and not scanPlan.allowLargeScan:
        scanStatusRegistry.markFailed(
            scanState.scan_id,
            "Scan rejected because one or more settings exceed the hard safety limits.",
        )
        logger.warning("dashboard_scan_rejected_hard_safety_limit notes=%s", scanPlan.safetyNotes)
        return RedirectResponse(f"/?scan_id={scanState.scan_id}", status_code=303)
    
    background_tasks.add_task(_runBackgroundScan, scanState.scan_id)
    return RedirectResponse(f"/?scan_id={scanState.scan_id}", status_code=303)


@dashboardRouter.get("/scan/status/{scan_id}")
async def getScanStatus(scan_id: str) -> JSONResponse:
    scanState = scanStatusRegistry.getScan(scan_id)
    if scanState is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return JSONResponse(scanState)


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
