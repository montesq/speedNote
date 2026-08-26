document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("maj-appliquer-btn");
  if (!btn) return;

  function attendreRedemarrage() {
    const essayer = () => {
      fetch(location.href, { method: "GET", cache: "no-store" })
        .then(() => location.reload())
        .catch(() => setTimeout(essayer, 1000));
    };
    setTimeout(essayer, 2000);
  }

  btn.addEventListener("click", async () => {
    btn.disabled = true;
    const texteInitial = btn.textContent;
    btn.textContent = "Téléchargement en cours…";
    try {
      const response = await fetch("/mise-a-jour/appliquer", { method: "POST" });
      const data = await response.json();
      if (!response.ok || data.erreur) {
        window.afficherToast("⚠️ " + (data.erreur || "Échec de la mise à jour."), "error");
        btn.disabled = false;
        btn.textContent = texteInitial;
        return;
      }
      btn.textContent = "Redémarrage en cours…";
      attendreRedemarrage();
    } catch (err) {
      window.afficherToast("❌ Échec de la mise à jour.", "error");
      btn.disabled = false;
      btn.textContent = texteInitial;
    }
  });
});
