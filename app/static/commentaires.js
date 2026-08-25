document.addEventListener("DOMContentLoaded", () => {
  const dialog = document.getElementById("modal-commentaire");
  if (!dialog) return;

  const titreEl = document.getElementById("commentaire-titre");
  const corpsEl = document.getElementById("commentaire-corps");

  function echapper(texte) {
    const div = document.createElement("div");
    div.textContent = texte;
    return div.innerHTML;
  }

  function ouvrir(titre, html) {
    titreEl.textContent = titre;
    corpsEl.innerHTML = html;
    dialog.showModal();
  }

  document.querySelectorAll(".note-comment-link:not(.moyenne-link)").forEach((btn) => {
    btn.addEventListener("click", () => {
      const appreciation = btn.dataset.appreciation || "Aucun commentaire.";
      ouvrir("✏️ " + btn.dataset.titre, `<p>${echapper(appreciation)}</p>`);
    });
  });

  document.querySelectorAll(".moyenne-link").forEach((btn) => {
    btn.addEventListener("click", () => {
      let notes = [];
      try {
        notes = JSON.parse(btn.dataset.comments || "[]");
      } catch (err) {
        notes = [];
      }
      const html = notes.length
        ? notes
            .map((n) => {
              const appreciation = n.appreciation || "Aucun commentaire.";
              return `<div class="commentaire-item"><strong>${echapper(n.devoir_titre)}</strong><p>${echapper(appreciation)}</p></div>`;
            })
            .join("")
        : "<p>Aucun devoir sur cette période.</p>";
      ouvrir("📔 " + btn.dataset.eleveNom, html);
    });
  });
});
