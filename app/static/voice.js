document.addEventListener("DOMContentLoaded", () => {
  const dialog = document.getElementById("modal-edit-note");
  if (!dialog) return;

  const devoirId = dialog.dataset.devoirId;

  const recordingView = document.getElementById("voice-recording-view");
  const editView = document.getElementById("voice-edit-view");
  const statusEl = document.getElementById("voice-status");
  const vuMask = document.getElementById("vu-mask");
  const transcriptHint = document.getElementById("voice-transcript-hint");
  const eleveNomEl = document.getElementById("edit-eleve-nom");
  const eleveIdInput = document.getElementById("edit-eleve-id");
  const valeurInput = document.getElementById("voice-valeur-input");
  const appreciationInput = document.getElementById("voice-appreciation-input");
  const stopBtn = document.getElementById("voice-stop-btn");
  const cancelBtn = document.getElementById("voice-cancel-btn");
  const closeBtn = document.getElementById("voice-close-btn");
  const recordBtn = document.getElementById("voice-record-btn");

  let mediaRecorder = null;
  let chunks = [];
  let activeStream = null;
  let cancelled = false;
  let audioContext = null;
  let analyser = null;
  let vuAnimationFrame = null;

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
    statusEl.innerHTML = "";
    statusEl.className = "voice-status";
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

  function startVuMeter(stream) {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    audioContext = new AudioCtx();
    const source = audioContext.createMediaStreamSource(stream);
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 512;
    analyser.smoothingTimeConstant = 0.6;
    source.connect(analyser);
    const data = new Uint8Array(analyser.frequencyBinCount);

    function tick() {
      analyser.getByteTimeDomainData(data);
      let sumSquares = 0;
      for (let i = 0; i < data.length; i++) {
        const normalized = (data[i] - 128) / 128;
        sumSquares += normalized * normalized;
      }
      const rms = Math.sqrt(sumSquares / data.length);
      const level = Math.min(1, rms * 4.5);
      vuMask.style.width = (100 - level * 100) + "%";
      vuAnimationFrame = requestAnimationFrame(tick);
    }
    tick();
  }

  function stopVuMeter() {
    if (vuAnimationFrame) {
      cancelAnimationFrame(vuAnimationFrame);
      vuAnimationFrame = null;
    }
    if (audioContext) {
      audioContext.close();
      audioContext = null;
      analyser = null;
    }
    vuMask.style.width = "100%";
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
    startVuMeter(stream);
    chunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.addEventListener("dataavailable", (event) => {
      if (event.data.size > 0) chunks.push(event.data);
    });
    mediaRecorder.addEventListener("stop", () => {
      stopVuMeter();
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
    stopVuMeter();
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
      showEditView();
      transcriptHint.textContent = "❌ Échec de la transcription : " + err.message;
    }
  }

  function appliquerResultat(data) {
    showEditView();
    if (data.erreur) {
      transcriptHint.textContent = "⚠️ " + data.erreur;
      return;
    }
    transcriptHint.textContent = data.transcript ? `Compris : « ${data.transcript} »` : "";
    if (data.valeur !== null && data.valeur !== undefined) {
      valeurInput.value = data.valeur;
    }
    if (data.appreciation) {
      appreciationInput.value = data.appreciation;
    }
  }

  function ouvrirPopup(btn) {
    eleveIdInput.value = btn.dataset.eleveId;
    eleveNomEl.textContent = "✏️ " + btn.dataset.eleveNom;
    valeurInput.value = btn.dataset.valeur || "";
    appreciationInput.value = btn.dataset.appreciation || "";
    transcriptHint.textContent = "";
    showEditView();
    dialog.showModal();
  }

  function closeDialog() {
    abandonRecording();
    dialog.close();
  }

  document.querySelectorAll(".note-link").forEach((btn) => {
    btn.addEventListener("click", () => ouvrirPopup(btn));
  });

  recordBtn.addEventListener("click", () => startRecording());
  stopBtn.addEventListener("click", stopRecording);
  cancelBtn.addEventListener("click", () => {
    abandonRecording();
    showEditView();
  });
  closeBtn.addEventListener("click", closeDialog);
  dialog.addEventListener("close", abandonRecording);
});
