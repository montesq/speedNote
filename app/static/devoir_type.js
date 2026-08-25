document.addEventListener("DOMContentLoaded", () => {
  const typeSelect = document.getElementById("devoir-type-select");
  const sousTypeLabel = document.getElementById("devoir-sous-type-label");
  const sousTypeSelect = document.getElementById("devoir-sous-type-select");
  if (!typeSelect || !sousTypeLabel || !sousTypeSelect) return;

  const typesAvecSousType = JSON.parse(typeSelect.dataset.typesAvecSousType || "[]");

  const majAffichage = () => {
    const visible = typesAvecSousType.includes(typeSelect.value);
    sousTypeLabel.hidden = !visible;
    if (!visible) sousTypeSelect.value = "";
  };

  typeSelect.addEventListener("change", majAffichage);
  majAffichage();
});
