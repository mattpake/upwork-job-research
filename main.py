import uvicorn

from src.core.config import loadApplicationSettings
from src.web.application import createApplication


app = createApplication()


def startDevelopmentServer() -> None:
    """Start the local dashboard development server."""

    applicationSettings = loadApplicationSettings()
    uvicorn.run(
        "main:app",
        host=applicationSettings.dashboardHost,
        port=applicationSettings.dashboardPort,
        reload=True,
    )


if __name__ == "__main__":
    startDevelopmentServer()
