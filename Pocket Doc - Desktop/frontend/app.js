const content = document.querySelector("#content");
const statusText = document.querySelector("#statusText");
const newSessionBtn = document.querySelector("#newSessionBtn");
const homeBtn = document.querySelector("#homeBtn");

const state = {
  screen: "home",
  session: null,
  health: null,
  models: [],
  selectedModelId: "",
};

const voice = {
  recorder: null,
  chunks: [],
  lastBlob: null,
  recording: false,
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json();
}

async function createSession() {
  state.session = await api("/api/sessions", {
    method: "POST",
    body: JSON.stringify({ patient: { displayName: "Yeni hasta" } }),
  });
  updateStatus();
  render();
}

function updateStatus(extra = "") {
  const sessionId = state.session ? state.session.id.slice(0, 8) : "yok";
  statusText.textContent = `Oturum ${sessionId}${extra ? " - " + extra : ""}`;
}

function setScreen(screen) {
  state.screen = screen;
  render();
}

function backHome() {
  setScreen("home");
}

function render() {
  if (!state.session) return;
  if (state.screen === "home") renderHome();
  if (state.screen === "voice") renderVoice();
  if (state.screen === "tools") renderTools();
  if (state.screen === "imaging") renderImaging();
}

function renderHome() {
  const models = state.health?.modelRegistry;
  const tools = state.health?.clinicalTools;
  content.innerHTML = `
    <section class="home-hero">
      <div class="panel">
        <h1 class="home-title">Hoş geldiniz doktor.</h1>
        <p class="home-subtitle">Bugün hangi modülü kullanmak istiyorsunuz?</p>
      </div>
      <div class="choice-grid">
        <button class="choice-card" data-go="voice">
          <div>
            <h2>PatientSum</h2>
            <p>Ses kaydı al, Whisper ile transkripte dök, epikriz/poliklinik özeti oluştur.</p>
          </div>
          <strong>Ses kaydı + özet</strong>
        </button>
        <button class="choice-card" data-go="tools">
          <div>
            <h2>Clinical Tools</h2>
            <p>ClinicalTools tam setindeki skorlar, ölçümler, karar kuralları ve klinik hesaplayıcılar.</p>
          </div>
          <strong>${tools ? `${tools.totalTools} araç yüklü` : "Tam set yüklü"}</strong>
        </button>
        <button class="choice-card" data-go="imaging">
          <div>
            <h2>Yapay Zeka Modelleri</h2>
            <p>Dental, dermatoloji, ortopedi, göğüs, beyin ve diğer görüntü modelleri.</p>
          </div>
          <strong>${models ? `${models.availableModels}/${models.totalModels} model hazır` : "Model registry"}</strong>
        </button>
      </div>
    </section>
  `;
  document.querySelectorAll("[data-go]").forEach((button) => {
    button.onclick = () => setScreen(button.dataset.go);
  });
}

function moduleHeader(title, subtitle = "") {
  return `
    <div class="module-header">
      <div>
        <h1>${title}</h1>
        ${subtitle ? `<p class="muted">${subtitle}</p>` : ""}
      </div>
      <button class="secondary-btn" id="backHomeBtn">Ana Sayfa</button>
    </div>
  `;
}

function bindBackButton() {
  const back = document.querySelector("#backHomeBtn");
  if (back) back.onclick = backHome;
}

function renderVoice() {
  content.innerHTML = `
    <section class="screen">
      <div class="panel">
        ${moduleHeader("PatientSum", "Ses kaydı, Whisper transkripsiyon ve epikriz/poliklinik özeti.")}
        <div class="actions">
          <button class="primary-btn" id="startRecordBtn">
            <span class="recording-dot ${voice.recording ? "on" : ""}"></span>Kaydı Başlat
          </button>
          <button class="danger-btn" id="stopRecordBtn" ${voice.recording ? "" : "disabled"}>Durdur ve Transkripte Dök</button>
          <button class="secondary-btn" id="summaryBtn">Özet Oluştur</button>
        </div>
        <p class="muted" id="voiceStatus">${voice.recording ? "Kayıt devam ediyor." : "Mikrofon hazır. Kayıt sonrası transkript otomatik yazılır."}</p>
        <div class="field">
          <label for="transcriptText">Transkript</label>
          <textarea id="transcriptText" placeholder="İsterseniz ses kaydı yerine transkripti buraya yazabilir veya yapıştırabilirsiniz.">${state.session?.transcript || ""}</textarea>
        </div>
      </div>
      <div class="panel">
        <h2>Epikriz / Poliklinik Özeti</h2>
        <div class="result">${state.session?.summary || "Henüz özet yok."}</div>
      </div>
    </section>
  `;
  bindBackButton();
  document.querySelector("#startRecordBtn").onclick = startRecording;
  document.querySelector("#stopRecordBtn").onclick = stopAndTranscribe;
  document.querySelector("#summaryBtn").onclick = summarizeTranscript;
}

async function startRecording() {
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    updateVoiceStatus("Bu tarayıcıda mikrofon kaydı desteklenmiyor.");
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    voice.chunks = [];
    voice.lastBlob = null;
    voice.recorder = new MediaRecorder(stream);
    voice.recorder.ondataavailable = (event) => {
      if (event.data?.size) voice.chunks.push(event.data);
    };
    voice.recorder.start();
    voice.recording = true;
    updateStatus("ses kaydı");
    renderVoice();
  } catch (error) {
    updateVoiceStatus(`Mikrofon açılamadı: ${error.message || error}`);
  }
}

async function stopAndTranscribe() {
  if (!voice.recorder || voice.recorder.state === "inactive") return;
  updateVoiceStatus("Kayıt durduruluyor...");
  const stopped = new Promise((resolve) => {
    voice.recorder.onstop = resolve;
  });
  voice.recorder.stop();
  voice.recorder.stream.getTracks().forEach((track) => track.stop());
  await stopped;
  voice.recording = false;
  voice.lastBlob = new Blob(voice.chunks, { type: "audio/webm" });
  renderVoice();
  await transcribeBlob(voice.lastBlob);
}

async function transcribeBlob(blob) {
  if (!blob || blob.size === 0) {
    updateVoiceStatus("Ses kaydı boş görünüyor.");
    return;
  }
  updateVoiceStatus("Whisper transkripsiyon çalışıyor...");
  const form = new FormData();
  form.append("file", blob, "consultation.webm");
  const response = await fetch(`/api/sessions/${state.session.id}/audio/transcribe?language=tr`, {
    method: "POST",
    body: form,
  });
  const payload = await response.json();
  if (!response.ok) {
    updateVoiceStatus(payload.detail || "Transkripsiyon hatası.");
    return;
  }
  state.session = payload.session;
  const warning = payload.result.warning ? ` - ${payload.result.warning}` : "";
  updateStatus(`transkript${warning}`);
  renderVoice();
}

function updateVoiceStatus(message) {
  const el = document.querySelector("#voiceStatus");
  if (el) el.textContent = message;
  updateStatus(message);
}

async function saveTranscript() {
  const transcript = document.querySelector("#transcriptText").value;
  state.session = await api(`/api/sessions/${state.session.id}/transcript`, {
    method: "POST",
    body: JSON.stringify({ transcript }),
  });
}

async function summarizeTranscript() {
  await saveTranscript();
  updateVoiceStatus("Özet oluşturuluyor...");
  const payload = await api(`/api/sessions/${state.session.id}/summary`, {
    method: "POST",
    body: JSON.stringify({ language: "tr" }),
  });
  state.session = payload.session;
  const warning = payload.result.warning ? ` - ${payload.result.warning}` : "";
  updateStatus(`özet hazır${warning}`);
  renderVoice();
}

function renderTools() {
  const tools = state.health?.clinicalTools;
  const toolText = tools ? `${tools.totalTools} araçlık tam set` : "ClinicalTools tam set";
  content.innerHTML = `
    <section class="screen tools-screen">
      <div class="panel">
        ${moduleHeader("Clinical Tools", `${toolText} ürün içine gömüldü.`)}
      </div>
      <iframe class="embedded-tool" src="/static/clinical_tools_full.html" title="Clinical Tools"></iframe>
    </section>
  `;
  bindBackButton();
}

function renderImaging() {
  const domainGroups = state.models.reduce((acc, model) => {
    acc[model.domain] ||= [];
    acc[model.domain].push(model);
    return acc;
  }, {});
  const modelOptions = Object.entries(domainGroups)
    .map(([domain, models]) => {
      const options = models
        .map((model) => `<option value="${model.id}">${model.exists ? "" : "[eksik] "}${model.name}</option>`)
        .join("");
      return `<optgroup label="${domain}">${options}</optgroup>`;
    })
    .join("");

  content.innerHTML = `
    <section class="screen">
      <div class="panel">
        ${moduleHeader("Yapay Zeka Modelleri", "Pi Camera, USB kamera ve dosya yükleme için görüntü analiz modülü.")}
        <div class="field">
          <label for="modelSelect">Model</label>
          <select id="modelSelect">${modelOptions}</select>
        </div>
        <div class="field">
          <label for="imageFile">Dosya yükle</label>
          <input id="imageFile" type="file" accept="image/*" />
        </div>
        <div class="actions">
          <button class="primary-btn" id="analyzeBtn">Analiz Et</button>
          <button class="secondary-btn" id="cameraPlaceholderBtn">Kamera Aç</button>
        </div>
        <p class="muted">Şu an dosya yükleme mock analizle çalışıyor. Pi Camera/USB kamera ve gerçek inference sıradaki modül.</p>
      </div>
      <div class="panel">
        <h2>Son Analiz</h2>
        <div class="result">${lastImagingText()}</div>
      </div>
    </section>
  `;
  bindBackButton();
  const modelSelect = document.querySelector("#modelSelect");
  if (state.selectedModelId) modelSelect.value = state.selectedModelId;
  else state.selectedModelId = modelSelect.value;
  modelSelect.onchange = () => (state.selectedModelId = modelSelect.value);
  document.querySelector("#analyzeBtn").onclick = analyzeImage;
  document.querySelector("#cameraPlaceholderBtn").onclick = () => updateStatus("kamera modülü sırada");
}

function lastImagingText() {
  const result = state.session?.imagingResults?.at(-1);
  if (!result) return "Henüz görüntü analizi yok.";
  return `${result.modelName}\n${result.resultSummaryTR}\n${(result.warningsTR || []).join("\n")}`;
}

async function analyzeImage() {
  const file = document.querySelector("#imageFile").files[0];
  if (!file) {
    updateStatus("dosya seçilmedi");
    return;
  }
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`/api/sessions/${state.session.id}/imaging/${state.selectedModelId}`, {
    method: "POST",
    body: form,
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(JSON.stringify(payload));
  state.session = payload.session;
  updateStatus("görüntü alındı");
  render();
}

async function init() {
  homeBtn.onclick = backHome;
  newSessionBtn.onclick = createSession;
  const [health, models] = await Promise.all([api("/api/health"), api("/api/models")]);
  state.health = health;
  state.models = models;
  state.selectedModelId = models[0]?.id || "";
  await createSession();
}

init().catch((error) => {
  statusText.textContent = "Hata";
  content.innerHTML = `<div class="panel"><h1>Başlatılamadı</h1><pre>${String(error)}</pre></div>`;
});
