const loadingForms = document.querySelectorAll("[data-loading-form]");
const scanOverlay = document.querySelector("[data-scan-overlay]");
const scanPhase = document.querySelector("[data-scan-phase]");
const scanPhases = [
  "Preparing configured keywords",
  "Running concurrent Apify actor jobs",
  "Normalizing Upwork job payloads",
  "Merging duplicate market signals",
  "Saving fresh research to SQLite"
];
let scanPhaseTimerId = null;
const scanSummaryState = document.body.dataset.scanSummary;
const scanErrorCount = document.body.dataset.scanErrors;

console.info("[Upwork Research] dashboard_loaded", {
  scanSummaryState,
  scanErrorCount
});

loadingForms.forEach((loadingForm) => {
  loadingForm.addEventListener("submit", () => {
    const submitButton = loadingForm.querySelector("button[type='submit']");
    const buttonLabel = loadingForm.querySelector("[data-button-label]");
    if (!submitButton || !buttonLabel) {
      return;
    }
    submitButton.classList.add("is-loading");
    submitButton.setAttribute("disabled", "disabled");
    buttonLabel.textContent = "Scanning Upwork";
    console.info("[Upwork Research] scan_submitted");
    showScanOverlay();
  });
});

function showScanOverlay() {
  if (!scanOverlay || !scanPhase) {
    return;
  }

  let activePhaseIndex = 0;
  scanOverlay.classList.add("is-visible");
  scanOverlay.setAttribute("aria-hidden", "false");
  scanPhase.textContent = scanPhases[activePhaseIndex];
  console.info("[Upwork Research] scan_phase", scanPhases[activePhaseIndex]);
  window.clearInterval(scanPhaseTimerId);
  scanPhaseTimerId = window.setInterval(() => {
    activePhaseIndex = (activePhaseIndex + 1) % scanPhases.length;
    scanPhase.textContent = scanPhases[activePhaseIndex];
    console.info("[Upwork Research] scan_phase", scanPhases[activePhaseIndex]);
  }, 1800);
}
