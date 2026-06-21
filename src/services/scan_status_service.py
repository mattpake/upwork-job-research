from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

from src.core.config import ScanPlan
from src.models.job_models import ScanRunSummary


ScanStatus = str


@dataclass
class ScanRunState:
    """Dashboard-visible status for one scan request."""

    scan_id: str
    status: ScanStatus
    started_at: str
    finished_at: str | None
    plan_summary: dict[str, object]
    raw_items_count: int = 0
    normalized_items_count: int = 0
    inserted_jobs_count: int = 0
    skipped_jobs_count: int = 0
    error_message: str | None = None
    errors: list[str] = field(default_factory=list)


class ScanStatusRegistry:
    """In-memory scan status tracker for the local dashboard."""

    def __init__(self) -> None:
        self._scanStates: dict[str, ScanRunState] = {}
        self._lock = Lock()

    def createScan(self, scanPlan: ScanPlan, status: ScanStatus = "pending") -> ScanRunState:
        scanState = ScanRunState(
            scan_id=str(uuid4()),
            status=status,
            started_at=_nowIso(),
            finished_at=None,
            plan_summary={
                "keywords": scanPlan.estimatedActorRuns,
                "results_per_keyword": scanPlan.resultsPerKeyword,
                "max_requested_jobs": scanPlan.estimatedMaxRequestedJobs,
                "concurrency": scanPlan.scanConcurrencyLimit,
                "dry_run": scanPlan.dryRun,
            },
        )
        with self._lock:
            self._scanStates[scanState.scan_id] = scanState
        return scanState

    def markRunning(self, scanId: str) -> None:
        self._update(scanId, status="running")

    def markDryRun(self, scanId: str) -> None:
        self._update(scanId, status="dry_run", finished_at=_nowIso())

    def markSucceeded(self, scanId: str, scanSummary: ScanRunSummary) -> None:
        self._update(
            scanId,
            status="succeeded",
            finished_at=_nowIso(),
            raw_items_count=scanSummary.rawItemsCount,
            normalized_items_count=scanSummary.normalizedItemsCount,
            inserted_jobs_count=scanSummary.insertedJobsCount,
            skipped_jobs_count=scanSummary.skippedJobsCount,
            errors=scanSummary.errors,
        )

    def markFailed(self, scanId: str, errorMessage: str) -> None:
        self._update(scanId, status="failed", finished_at=_nowIso(), error_message=errorMessage)

    def getScan(self, scanId: str) -> dict[str, object] | None:
        with self._lock:
            scanState = self._scanStates.get(scanId)
            if scanState is None:
                return None
            return asdict(scanState)

    def clear(self) -> None:
        with self._lock:
            self._scanStates.clear()

    def _update(self, scanId: str, **updates: object) -> None:
        with self._lock:
            scanState = self._scanStates[scanId]
            for key, value in updates.items():
                setattr(scanState, key, value)


def _nowIso() -> str:
    return datetime.now(UTC).isoformat()


scanStatusRegistry = ScanStatusRegistry()
