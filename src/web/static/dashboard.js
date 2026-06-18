const loadingForms = document.querySelectorAll("[data-loading-form]");

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
  });
});
