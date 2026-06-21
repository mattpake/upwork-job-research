const PAGE_SIZE = 25;

let currentPage = 1;
let allRows = [];

// ---- Scan overlay ----
const loadingForms = document.querySelectorAll("[data-loading-form]");
const scanOverlay = document.querySelector("[data-scan-overlay]");
const scanPhase = document.querySelector("[data-scan-phase]");
const activeScanId = document.body.dataset.activeScanId;
const scanStatusPanel = document.querySelector("[data-scan-status-panel]");
const scanStatusLabel = document.querySelector("[data-scan-status-label]");
const scanStatusMessage = document.querySelector("[data-scan-status-message]");
const scanPhases = [
  "Preparing configured keywords",
  "Running concurrent Apify actor jobs",
  "Normalizing Upwork job payloads",
  "Merging duplicate market signals",
  "Saving fresh research to SQLite"
];
let scanPhaseTimerId = null;
let scanStatusTimerId = null;

loadingForms.forEach((loadingForm) => {
  loadingForm.addEventListener("submit", (event) => {
    const confirmationMessage = loadingForm.dataset.scanConfirm;
    if (confirmationMessage && !window.confirm(confirmationMessage)) {
      event.preventDefault();
      return;
    }
    const submitButton = loadingForm.querySelector("button[type='submit']");
    const buttonLabel = loadingForm.querySelector("[data-button-label]");
    if (!submitButton || !buttonLabel) return;
    submitButton.setAttribute("disabled", "disabled");
    buttonLabel.textContent = "Starting scan…";
    showScanOverlay();
  });
});

function showScanOverlay() {
  if (!scanOverlay || !scanPhase) return;
  let activePhaseIndex = 0;
  scanOverlay.classList.add("is-visible");
  scanOverlay.setAttribute("aria-hidden", "false");
  scanPhase.textContent = scanPhases[activePhaseIndex];
  window.clearInterval(scanPhaseTimerId);
  scanPhaseTimerId = window.setInterval(() => {
    activePhaseIndex = (activePhaseIndex + 1) % scanPhases.length;
    scanPhase.textContent = scanPhases[activePhaseIndex];
  }, 1800);
}

function hideScanOverlay() {
  if (!scanOverlay) return;
  scanOverlay.classList.remove("is-visible");
  scanOverlay.setAttribute("aria-hidden", "true");
  window.clearInterval(scanPhaseTimerId);
}

function updateScanStatusCopy(label, message, isError = false) {
  if (!scanStatusPanel || !scanStatusLabel || !scanStatusMessage) return;
  scanStatusLabel.textContent = label;
  scanStatusMessage.textContent = message;
  scanStatusPanel.classList.toggle("is-error", isError);
  scanStatusPanel.classList.toggle("is-success", !isError && (label === "Scan completed" || label === "Dry run complete"));
}

async function pollScanStatus(scanId) {
  try {
    const response = await fetch(`/scan/status/${scanId}`, { headers: { Accept: "application/json" } });
    if (!response.ok) {
      updateScanStatusCopy("Scan failed", "Unable to read scan status.", true);
      return;
    }
    const scanStatus = await response.json();
    if (scanStatus.status === "pending" || scanStatus.status === "running") {
      updateScanStatusCopy("Scan running", "Scan running. The table will refresh automatically when results are saved.");
      return;
    }
    window.clearInterval(scanStatusTimerId);
    window.clearInterval(scanPhaseTimerId);
    if (scanStatus.status === "succeeded") {
      updateScanStatusCopy(
        "Scan completed",
        `Scan completed. ${scanStatus.inserted_jobs_count || 0} jobs inserted. Refreshing table...`
      );
      window.setTimeout(reloadWithoutScanId, 700);
      return;
    }
    if (scanStatus.status === "dry_run") {
      updateScanStatusCopy("Dry run complete", "Dry run complete. No Apify calls were made.");
      hideScanOverlay();
      return;
    }
    updateScanStatusCopy("Scan failed", scanStatus.error_message || "Scan failed.", true);
    hideScanOverlay();
  } catch (error) {
    updateScanStatusCopy("Scan failed", "Unable to read scan status.", true);
    hideScanOverlay();
    window.clearInterval(scanStatusTimerId);
  }
}

function reloadWithoutScanId() {
  const nextUrl = new URL(window.location.href);
  nextUrl.searchParams.delete("scan_id");
  window.location.href = nextUrl.toString();
}

function initScanStatusPolling() {
  if (!activeScanId) return;
  showScanOverlay();
  updateScanStatusCopy("Scan started", "Scan running. The table will refresh automatically when results are saved.");
  pollScanStatus(activeScanId);
  scanStatusTimerId = window.setInterval(() => pollScanStatus(activeScanId), 1500);
}

// ---- Pagination ----
const paginationControls = document.getElementById("pagination-controls");
const btnPrev = document.getElementById("btn-prev-page");
const btnNext = document.getElementById("btn-next-page");
const pageInfoStart = document.getElementById("page-info-start");
const pageInfoEnd = document.getElementById("page-info-end");
const pageInfoTotal = document.getElementById("page-info-total");
const pageNumberDisplay = document.getElementById("page-number-display");

function getTotalPages() {
  return Math.max(1, Math.ceil(allRows.length / PAGE_SIZE));
}

function renderPage(page) {
  currentPage = Math.max(1, Math.min(page, getTotalPages()));

  const start = (currentPage - 1) * PAGE_SIZE;
  const end = Math.min(start + PAGE_SIZE, allRows.length);

  allRows.forEach((row, i) => {
    row.classList.toggle("hidden", i < start || i >= end);
  });

  // Update info text
  if (pageInfoStart) pageInfoStart.textContent = allRows.length === 0 ? 0 : start + 1;
  if (pageInfoEnd) pageInfoEnd.textContent = end;
  if (pageInfoTotal) pageInfoTotal.textContent = allRows.length;
  if (pageNumberDisplay) {
    pageNumberDisplay.textContent = `Page ${currentPage} of ${getTotalPages()}`;
  }

  // Update button states
  if (btnPrev) btnPrev.disabled = currentPage <= 1;
  if (btnNext) btnNext.disabled = currentPage >= getTotalPages();
}

function initPagination() {
  allRows = Array.from(document.querySelectorAll("[data-job-row]"));
  if (allRows.length === 0) return;

  if (paginationControls) paginationControls.classList.remove("hidden");

  btnPrev?.addEventListener("click", () => {
    renderPage(currentPage - 1);
    document.getElementById("jobs-tbody")?.closest(".surface-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  btnNext?.addEventListener("click", () => {
    renderPage(currentPage + 1);
    document.getElementById("jobs-tbody")?.closest(".surface-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  renderPage(1);
}

// ---- Job detail panel ----
const detailContent = document.getElementById("detail-content");
const detailEmpty = document.getElementById("detail-empty");
const detailTitle = document.getElementById("detail-title");
const detailUrl = document.getElementById("detail-url");
const detailBudget = document.getElementById("detail-budget");
const detailClient = document.getElementById("detail-client");
const detailSpent = document.getElementById("detail-spent");
const detailProposals = document.getElementById("detail-proposals");
const detailExperience = document.getElementById("detail-experience");
const detailDuration = document.getElementById("detail-duration");
const detailSkillsList = document.getElementById("detail-skills-list");
const detailDescription = document.getElementById("detail-description");
const detailJson = document.getElementById("detail-json");

function populateDetail(jobData) {
  if (detailContent) detailContent.classList.remove("hidden");
  if (detailEmpty) detailEmpty.classList.add("hidden");

  if (detailTitle) detailTitle.textContent = jobData.title || "";

  if (detailUrl) {
    detailUrl.href = jobData.jobUrl || "#";
    detailUrl.style.display = jobData.jobUrl ? "" : "none";
  }

  if (detailBudget) {
    let budgetText = jobData.budgetType || "—";
    if (jobData.fixedBudget) budgetText += ` · $${Math.round(jobData.fixedBudget)}`;
    if (jobData.hourlyMin) budgetText += ` · $${Math.round(jobData.hourlyMin)}–$${Math.round(jobData.hourlyMax || jobData.hourlyMin)}/hr`;
    detailBudget.textContent = budgetText;
  }

  if (detailClient) {
    const countryFromRaw = jobData.clientCountry || jobData.client_country || (jobData.rawJson && jobData.rawJson.client && (jobData.rawJson.client.country || jobData.rawJson.client.countryCode || jobData.rawJson.client.country_code));
    const resolvedCountry = _resolveCountryName(countryFromRaw);
    detailClient.textContent = resolvedCountry || "—";
  }

  // clientSpent: prefer stored field, then rawJson.client.totalSpent or rawJson.client.stats.totalSpent
  if (detailSpent) {
    const spentFromRaw = jobData.clientSpent || jobData.client_spent || (jobData.rawJson && jobData.rawJson.client && (jobData.rawJson.client.totalSpent || (jobData.rawJson.client.stats && (jobData.rawJson.client.stats.totalSpent || jobData.rawJson.client.stats.total_spent))));
    detailSpent.textContent = spentFromRaw || "—";
  }

  if (detailProposals) detailProposals.textContent = jobData.proposalsCount || jobData.proposals_count || (jobData.rawJson && (jobData.rawJson.proposals || jobData.rawJson.applicants)) || "—";

  // experience: prefer stored field, then vendor.experienceLevel
  if (detailExperience) {
    const experienceFromRaw = jobData.experienceLevel || jobData.experience_level || (jobData.rawJson && jobData.rawJson.vendor && (jobData.rawJson.vendor.experienceLevel || jobData.rawJson.vendor.experience_level));
    detailExperience.textContent = experienceFromRaw || "—";
  }
  if (detailDuration) detailDuration.textContent = jobData.jobDuration || "—";

  // Skills as chips
  if (detailSkillsList) {
    detailSkillsList.innerHTML = "";
    const skills = jobData.skills || [];
    if (skills.length > 0) {
      skills.forEach(skill => {
        const chip = document.createElement("span");
        chip.className = "skill-chip";
        chip.textContent = skill;
        detailSkillsList.appendChild(chip);
      });
    } else {
      detailSkillsList.innerHTML = `<span style="font-size:13px;color:var(--color-muted)">No skills listed</span>`;
    }
  }

  if (detailDescription) {
    detailDescription.textContent = jobData.description || "No description captured.";
  }

  if (detailJson) {
    detailJson.textContent = JSON.stringify(jobData.rawJson, null, 2);
  }
}

function _resolveCountryName(rawCountry) {
  if (!rawCountry) return null;
  const text = String(rawCountry).trim();
  if (!text) return null;
  if (text.length > 3 || text.indexOf(" ") !== -1) return text;
  const code = text.toUpperCase();
  const mapping = {
    US: "United States",
    CA: "Canada",
    GB: "United Kingdom",
    UK: "United Kingdom",
    AU: "Australia",
    IN: "India",
    DE: "Germany",
    FR: "France",
    NL: "Netherlands",
    ES: "Spain",
    IT: "Italy",
    BR: "Brazil",
    MX: "Mexico",
    PH: "Philippines",
    PK: "Pakistan",
    NG: "Nigeria",
  };
  return mapping[code] || text;
}

function initJobSelection() {
  document.querySelectorAll("[data-job-row]").forEach(row => {
    row.addEventListener("click", (e) => {
      if (e.target.closest("form") || e.target.closest("select")) return;

      // Highlight active row
      document.querySelectorAll("[data-job-row]").forEach(r => r.classList.remove("is-active"));
      row.classList.add("is-active");

      const jobData = JSON.parse(row.dataset.jobJson);
      populateDetail(jobData);
    });
  });
}

// ---- Init ----
initPagination();
initJobSelection();
initScanStatusPolling();
