document.addEventListener("DOMContentLoaded", () => {
  const openBtn = document.getElementById("voice-btn");
  const dialog = document.getElementById("modal-voice");
  if (!openBtn || !dialog) return;

  const devoirId = openBtn.dataset.devoirId;
  const recordingView = document.getElementById("voice-recording-view");
  const editView = document.getElementById("voice-edit-view");
  const statusEl = document.getElementById("voice-status");
  const transcriptHint = document.getElementById("voice-transcript-hint");
  const eleveSelect = document.getElementById("voice-eleve-select");
  const valeurInput = document.getElementById("voice-valeur-input");
  const appreciationInput = document.getElementById("voice-appreciation-input");
  const stopBtn = document.getElementById("voice-stop-btn");
  const cancelBtn = document.getElementById("voice-cancel-btn");
  const closeBtn = document.getElementById("voice-close-btn");
  const redoBtn = document.getElementById("voice-redo-btn");

  let mediaRecorder = null;
  let chunks = [];
  let activeStream = null;
  let cancelled = false;

  function setStatus(text, cls) {
    statusEl.innerHTML = "";
    if (cls !== "voice-error") {
      const dot = document.createElement("span");
      dot.className = "voice-dot";
      statusEl.appendChild(dot);
    }
    statusEl.appendChild(document.createTextNode(text));
    statusEl.className = "voice-status" + (cls ? " " + cls : "");
  }

  function showRecordingView() {
    recordingView.hidden = false;
    editView.hidden = true;
    setStatus("Enregistrement en cours…");
  }

  function showEditView() {
    recordingView.hidden = true;
    editView.hidden = false;
  }

  function stopStream() {
    if (activeStream) {
      activeStream.getTracks().forEach((track) => track.stop());
      activeStream = null;
    }
  }

  async function startRecording() {
    cancelled = false;
    showRecordingView();
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      setStatus("🎙️ Micro inaccessible : " + err.message, "voice-error");
      return;
    }
    activeStream = stream;
    chunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.addEventListener("dataavailable", (event) => {
      if (event.data.size > 0) chunks.push(event.data);
    });
    mediaRecorder.addEventListener("stop", () => {
      stopStream();
      if (!cancelled) sendRecording();
    });
    mediaRecorder.start();
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      setStatus("Transcription en cours…");
      mediaRecorder.stop();
    }
  }

  function abandonRecording() {
    cancelled = true;
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
    stopStream();
  }

  async function sendRecording() {
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
    }
  }

  function appliquerResultat(data) {
    if (data.erreur) {
      setStatus("⚠️ " + data.erreur, "voice-error");
      return;
    }
    transcriptHint.textContent = data.transcript ? `Compris : « ${data.transcript} »` : "";
    eleveSelect.value = data.eleve_id || "";
    valeurInput.value = data.valeur !== null && data.valeur !== undefined ? data.valeur : "";
    appreciationInput.value = data.appreciation || "";
    showEditView();
  }

  function closeDialog() {
    abandonRecording();
    dialog.close();
  }

  openBtn.addEventListener("click", () => {
    dialog.showModal();
    startRecording();
  });
  stopBtn.addEventListener("click", stopRecording);
  cancelBtn.addEventListener("click", closeDialog);
  closeBtn.addEventListener("click", closeDialog);
  redoBtn.addEventListener("click", () => startRecording());
  dialog.addEventListener("close", abandonRecording);
});
