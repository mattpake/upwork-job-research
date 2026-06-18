from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from src.core.config import loadApplicationSettings
from src.repositories.job_repository import JobRepository
from src.web.dashboard_routes import dashboardRouter


def createApplication() -> FastAPI:
    """Create and configure the FastAPI web application."""

    applicationSettings = loadApplicationSettings()
    JobRepository(applicationSettings.databasePath).initializeDatabase()

    fastApiApplication = FastAPI(title="Upwork Job Research Dashboard")
    fastApiApplication.add_middleware(
        SessionMiddleware,
        secret_key=applicationSettings.sessionSecret,
        same_site="lax",
    )
    fastApiApplication.mount("/static", StaticFiles(directory="src/web/static"), name="static")
    fastApiApplication.include_router(dashboardRouter)
    return fastApiApplication
