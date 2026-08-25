document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("dialog.modal").forEach((dialog) => {
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) {
        dialog.close();
      }
    });
  });
});
