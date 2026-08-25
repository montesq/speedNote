document.addEventListener("DOMContentLoaded", () => {
  const dialog = document.getElementById("modal-commentaire");
  if (!dialog) return;

  const titreEl = document.getElementById("commentaire-titre");
  const corpsEl = document.getElementById("commentaire-corps");
  const bilanBtn = document.getElementById("bilan-generer-btn");
  const bilanZone = document.getElementById("bilan-zone");
  const bilanTexte = document.getElementById("bilan-texte");
  const bilanStatut = document.getElementById("bilan-statut");

  let contexteBilan = null;

  function echapper(texte) {
    const div = document.createElement("div");
    div.textContent = texte;
    return div.innerHTML;
  }

  // Le texte est échappé (protection XSS) puis les sauts de ligne sont
  // convertis en <br> pour être visibles dans le rendu.
  function formater(texte) {
    return echapper(texte).replace(/\n/g, "<br>");
  }

  function ouvrir(titre, html, bilan) {
    titreEl.textContent = titre;
    corpsEl.innerHTML = html;
    contexteBilan = bilan;
    bilanBtn.hidden = !bilan;
    bilanZone.hidden = true;
    bilanTexte.value = "";
    bilanStatut.textContent = "";
    dialog.showModal();
    // showModal() donne le focus au bouton "Fermer" (seul élément
    // focusable), ce qui fait défiler la popup jusqu'à lui plutôt que de
    // l'afficher depuis le début.
    dialog.scrollTop = 0;
  }

  document.querySelectorAll(".note-comment-link:not(.moyenne-link)").forEach((btn) => {
    btn.addEventListener("click", () => {
      const appreciation = btn.dataset.appreciation || "Aucun commentaire.";
      ouvrir("✏️ " + btn.dataset.titre, `<p>${formater(appreciation)}</p>`, null);
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
              return `<div class="commentaire-item"><strong>${echapper(n.devoir_titre)}</strong><p>${formater(appreciation)}</p></div>`;
            })
            .join("")
        : "<p>Aucun devoir sur cette période.</p>";
      ouvrir("📔 " + btn.dataset.eleveNom, html, { nom: btn.dataset.eleveNom, commentaires: notes });
    });
  });

  bilanBtn.addEventListener("click", async () => {
    if (!contexteBilan) return;
    bilanZone.hidden = false;
    bilanTexte.value = "";
    bilanStatut.textContent = "⏳ Génération en cours, cela peut prendre jusqu'à quelques minutes…";
    bilanBtn.disabled = true;
    try {
      const formData = new FormData();
      formData.append("nom", contexteBilan.nom);
      formData.append("commentaires", JSON.stringify(contexteBilan.commentaires));
      const response = await fetch("/bilan/generer", { method: "POST", body: formData });
      const data = await response.json();
      if (!response.ok || data.erreur) {
        bilanStatut.textContent = "⚠️ " + (data.erreur || "Échec de la génération.");
      } else {
        bilanTexte.value = data.bilan;
        bilanStatut.textContent = "";
      }
    } catch (err) {
      bilanStatut.textContent = "❌ Échec de la génération.";
    } finally {
      bilanBtn.disabled = false;
    }
  });
});
