document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("saisie-form");
  if (!form) return;
  const inputs = Array.from(form.querySelectorAll("input.note-input, input.app-input"));
  inputs.forEach((input, idx) => {
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        const next = inputs[idx + 1];
        if (next) {
          next.focus();
          next.select();
        } else {
          form.requestSubmit();
        }
      }
    });
  });
});
