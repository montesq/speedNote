function afficherToast(message, type) {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toastEl = document.createElement("div");
  toastEl.className = "toast align-items-center border-0 text-bg-" + (type === "error" ? "danger" : "success");
  toastEl.setAttribute("role", "alert");
  toastEl.innerHTML =
    '<div class="d-flex">' +
    '<div class="toast-body"></div>' +
    '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Fermer"></button>' +
    "</div>";
  toastEl.querySelector(".toast-body").textContent = message;
  container.appendChild(toastEl);

  const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
  toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
  toast.show();
}

window.afficherToast = afficherToast;
