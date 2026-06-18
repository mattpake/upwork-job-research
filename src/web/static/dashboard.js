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

const jobRows = document.querySelectorAll("[data-job-row]");
const detailContent = document.getElementById("detail-content");
const detailEmpty = document.getElementById("detail-empty");
const detailTitle = document.getElementById("detail-title");
const detailUrl = document.getElementById("detail-url");
const detailBudget = document.getElementById("detail-budget");
const detailClient = document.getElementById("detail-client");
const detailSpent = document.getElementById("detail-spent");
const detailProposals = document.getElementById("detail-proposals");
const detailSkills = document.getElementById("detail-skills");
const detailDescription = document.getElementById("detail-description");
const detailJson = document.getElementById("detail-json");

jobRows.forEach(row => {
  row.addEventListener("click", (e) => {
    // Ignore clicks on forms, links, or select dropdowns
    if (e.target.closest("form") || e.target.closest("select") || e.target.closest("a")) return;
    
    // Read the embedded JSON payload
    const jobData = JSON.parse(row.dataset.jobJson);
    
    // Toggle empty state
    if (detailContent) detailContent.classList.remove("hidden");
    if (detailEmpty) detailEmpty.classList.add("hidden");
    
    // Populate simple fields
    if (detailTitle) detailTitle.textContent = jobData.title || "";
    if (detailUrl) detailUrl.href = jobData.jobUrl || "#";
    if (detailBudget) detailBudget.textContent = jobData.budgetType || "Unknown";
    if (detailClient) detailClient.textContent = jobData.clientCountry || "Unknown";
    if (detailSpent) detailSpent.textContent = jobData.clientSpent || "Unknown";
    if (detailProposals) detailProposals.textContent = jobData.proposalsCount || "Unknown";
    
    // Populate complex fields
    if (detailSkills) {
      detailSkills.textContent = (jobData.skills && jobData.skills.length > 0) 
        ? jobData.skills.join(", ") 
        : "Unknown";
    }
    
    if (detailDescription) {
      detailDescription.textContent = jobData.description || "No description captured.";
    }
    
    if (detailJson) {
      detailJson.textContent = JSON.stringify(jobData.rawJson, null, 2);
    }
  });
});
