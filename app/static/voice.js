document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("voice-btn");
  const status = document.getElementById("voice-status");
  if (!btn || !status) return;

  const devoirId = btn.dataset.devoirId;
  let mediaRecorder = null;
  let chunks = [];
  let recording = false;

  function setStatus(text, cls) {
    status.textContent = text;
    status.className = "voice-status" + (cls ? " " + cls : "");
  }

  async function startRecording() {
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      setStatus("🎙️ Micro inaccessible : " + err.message, "voice-error");
      return;
    }
    chunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.addEventListener("dataavailable", (event) => {
      if (event.data.size > 0) chunks.push(event.data);
    });
    mediaRecorder.addEventListener("stop", () => {
      stream.getTracks().forEach((track) => track.stop());
      sendRecording();
    });
    mediaRecorder.start();
    recording = true;
    btn.textContent = "⏹ Arrêter";
    btn.classList.add("recording");
    setStatus("🔴 Enregistrement en cours…", "");
  }

  function stopRecording() {
    if (mediaRecorder && recording) {
      mediaRecorder.stop();
      recording = false;
      btn.textContent = "🎤 Commentaire vocal";
      btn.classList.remove("recording");
    }
  }

  async function sendRecording() {
    setStatus("⏳ Transcription en cours…", "");
    btn.disabled = true;
    const blob = new Blob(chunks, { type: mediaRecorder.mimeType || "audio/webm" });
    const formData = new FormData();
    formData.append("audio", blob, "commentaire.webm");
    try {
      const response = await fetch(`/devoirs/${devoirId}/transcrire`, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      appliquerResultat(data);
    } catch (err) {
      setStatus("❌ Échec de la transcription : " + err.message, "voice-error");
    } finally {
      btn.disabled = false;
    }
  }

  function appliquerResultat(data) {
    if (data.erreur) {
      let msg = "⚠️ " + data.erreur;
      if (data.transcript) msg += ` (compris : "${data.transcript}")`;
      setStatus(msg, "voice-error");
      return;
    }
    const noteInput = document.querySelector(`input[name="note_${data.eleve_id}"]`);
    const appInput = document.querySelector(`input[name="app_${data.eleve_id}"]`);
    if (!noteInput || !appInput) {
      setStatus("⚠️ Élève reconnu mais introuvable dans la grille.", "voice-error");
      return;
    }
    if (data.valeur !== null && data.valeur !== undefined) {
      noteInput.value = data.valeur;
    }
    if (data.appreciation) {
      appInput.value = data.appreciation;
    }
    const row = noteInput.closest("tr");
    if (row) {
      row.classList.add("row-highlight");
      row.scrollIntoView({ behavior: "smooth", block: "center" });
      setTimeout(() => row.classList.remove("row-highlight"), 3000);
    }
    appInput.focus();
    setStatus(
      `✅ ${data.eleve_nom} : note et appréciation pré-remplies. Vérifiez puis enregistrez.`,
      "voice-success"
    );
  }

  btn.addEventListener("click", () => {
    if (recording) {
      stopRecording();
    } else {
      startRecording();
    }
  });
});
