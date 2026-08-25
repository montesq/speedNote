document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("coefficient-input");
  if (!input) return;

  let valeurEnregistree = input.value;

  input.addEventListener("change", async () => {
    if (input.value === valeurEnregistree || input.value.trim() === "") {
      input.value = valeurEnregistree;
      return;
    }
    const devoirId = input.dataset.devoirId;
    const formData = new FormData();
    formData.append("coefficient", input.value);

    try {
      const response = await fetch(`/devoirs/${devoirId}/coefficient`, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (!response.ok || data.erreur) {
        window.afficherToast("⚠️ " + (data.erreur || "Échec de l'enregistrement."), "error");
        input.value = valeurEnregistree;
        return;
      }
      valeurEnregistree = String(data.coefficient);
      input.value = valeurEnregistree;
      window.afficherToast("✅ Coefficient mis à jour.");
    } catch (err) {
      window.afficherToast("❌ Échec de l'enregistrement.", "error");
      input.value = valeurEnregistree;
    }
  });
});
