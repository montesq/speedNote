document.addEventListener("DOMContentLoaded", () => {
  const recordingView = document.getElementById("outil-recording-view");
  const reposView = document.getElementById("outil-repos-view");
  if (!recordingView || !reposView) return;

  const statusEl = document.getElementById("outil-status");
  const vuMask = document.getElementById("outil-vu-mask");
  const transcriptHint = document.getElementById("outil-transcript-hint");
  const texteEl = document.getElementById("outil-texte");
  const recordBtn = document.getElementById("outil-record-btn");
  const stopBtn = document.getElementById("outil-stop-btn");
  const cancelBtn = document.getElementById("outil-cancel-btn");

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
    reposView.hidden = true;
    statusEl.innerHTML = "";
    statusEl.className = "voice-status";
  }

  function showReposView() {
    recordingView.hidden = true;
    reposView.hidden = false;
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
    showReposView();
  }

  async function sendRecording() {
    const blob = new Blob(chunks, { type: mediaRecorder.mimeType || "audio/webm" });
    const formData = new FormData();
    formData.append("audio", blob, "dictee.webm");
    try {
      const response = await fetch("/outil/transcrire", { method: "POST", body: formData });
      const data = await response.json();
      appliquerResultat(data);
    } catch (err) {
      showReposView();
      transcriptHint.textContent = "❌ Échec de la transcription : " + err.message;
    }
  }

  function appliquerResultat(data) {
    showReposView();
    if (data.erreur) {
      transcriptHint.textContent = "⚠️ " + data.erreur;
      return;
    }
    transcriptHint.textContent = "";
    if (data.texte) {
      texteEl.value = texteEl.value ? texteEl.value + "\n\n" + data.texte : data.texte;
    }
  }

  recordBtn.addEventListener("click", () => startRecording());
  stopBtn.addEventListener("click", stopRecording);
  cancelBtn.addEventListener("click", abandonRecording);
});
