const phrases = [
  "Resolving place and time",
  "Calculating the chart",
  "Mapping structural patterns",
  "Selecting report material",
  "Assembling the reading",
  "Preparing the report view",
];

document.querySelectorAll("[data-loading-form]").forEach((form) => {
  form.addEventListener("submit", () => {
    const overlay = document.querySelector(".loading-overlay");
    const phrase = document.querySelector("[data-loading-phrase]");
    if (!overlay || !phrase) return;
    overlay.hidden = false;
    let index = 0;
    window.setInterval(() => {
      index = (index + 1) % phrases.length;
      phrase.textContent = phrases[index];
    }, 1300);
  });
});

document.querySelectorAll("[data-print-report]").forEach((button) => {
  button.addEventListener("click", () => {
    const frame = document.querySelector(".viewer-frame iframe");
    if (frame && frame.contentWindow) {
      frame.contentWindow.focus();
      frame.contentWindow.print();
    }
  });
});

document.querySelectorAll("[data-copy-prompt]").forEach((button) => {
  button.addEventListener("click", async () => {
    const textarea = button.closest(".copy-prompt")?.querySelector("textarea");
    if (!textarea) return;
    await navigator.clipboard.writeText(textarea.value);
    const original = button.textContent;
    button.textContent = "Copied";
    window.setTimeout(() => {
      button.textContent = original;
    }, 1600);
  });
});

document.querySelectorAll("[data-delete-report]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const frame = document.querySelector(".viewer-frame iframe");
    if (frame) frame.src = "about:blank";
    window.setTimeout(() => form.submit(), 250);
  });
});
