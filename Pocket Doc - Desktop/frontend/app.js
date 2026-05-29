const content = document.querySelector("#content");
const statusText = document.querySelector("#statusText");
const newSessionBtn = document.querySelector("#newSessionBtn");
const homeBtn = document.querySelector("#homeBtn");

const state = {
  screen: "home",
  session: null,
  sessions: [],
  sessionFilters: {
    query: "",
    status: "",
    includeArchived: false,
  },
  health: null,
  models: [],
  selectedModelId: "",
  reportPreview: "",
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

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadSessions() {
  const params = new URLSearchParams();
  if (state.sessionFilters.query) params.set("query", state.sessionFilters.query);
  if (state.sessionFilters.status) params.set("status", state.sessionFilters.status);
  if (state.sessionFilters.includeArchived) params.set("include_archived", "true");
  const suffix = params.toString() ? `?${params.toString()}` : "";
  state.sessions = await api(`/api/sessions${suffix}`);
  return state.sessions;
}

async function createSession() {
  state.session = await api("/api/sessions", {
    method: "POST",
    body: JSON.stringify({ patient: { displayName: "Yeni hasta" } }),
  });
  state.reportPreview = "";
  state.sessionFilters.status = "";
  state.sessionFilters.includeArchived = false;
  await loadSessions();
  updateStatus("yeni oturum");
  render();
}

async function openSession(sessionId, targetScreen = "voice") {
  state.session = await api(`/api/sessions/${sessionId}`);
  state.reportPreview = "";
  state.screen = targetScreen;
  updateStatus("oturum açıldı");
  render();
}

function updateStatus(extra = "") {
  const sessionId = state.session ? state.session.id.slice(0, 8) : "yok";
  const finalized = state.session?.finalized ? " - final" : "";
  const archived = state.session?.archived ? " - arşiv" : "";
  statusText.textContent = `Oturum ${sessionId}${finalized}${archived}${extra ? " - " + extra : ""}`;
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
  const recentSessions = state.sessions.slice(0, 12);
  const recentHtml = recentSessions.length
    ? recentSessions.map((session) => renderSessionCard(session)).join("")
    : `<div class="empty-state">Bu filtrelerle kayıtlı oturum bulunamadı.</div>`;

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
            <p>Hasta bilgisi, ses kaydı, transkript, klinik özet, hekim notu ve rapor önizleme.</p>
          </div>
          <strong>${state.session?.finalized ? "Final onaylı" : "Klinik not akışı"}</strong>
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
      <div class="panel recent-panel">
        <div class="module-header compact-header">
          <div>
            <h1>Son Oturumlar</h1>
            <p class="muted">Hasta adı, şikayet veya durum filtresiyle arayın; arşivlenenleri isteğe bağlı gösterin.</p>
          </div>
          <button class="secondary-btn" id="refreshSessionsBtn">Yenile</button>
        </div>
        <div class="session-filters">
          <input id="sessionSearchInput" value="${escapeHtml(state.sessionFilters.query)}" placeholder="Hasta adı, şikayet veya not ara" />
          <select id="sessionStatusFilter">
            <option value="" ${!state.sessionFilters.status ? "selected" : ""}>Tüm aktifler</option>
            <option value="draft" ${state.sessionFilters.status === "draft" ? "selected" : ""}>Taslak</option>
            <option value="transcript" ${state.sessionFilters.status === "transcript" ? "selected" : ""}>Transkript</option>
            <option value="summary" ${state.sessionFilters.status === "summary" ? "selected" : ""}>Özetli</option>
            <option value="final" ${state.sessionFilters.status === "final" ? "selected" : ""}>Final</option>
            <option value="archived" ${state.sessionFilters.status === "archived" ? "selected" : ""}>Arşiv</option>
          </select>
          <label class="inline-check"><input id="includeArchivedInput" type="checkbox" ${state.sessionFilters.includeArchived ? "checked" : ""} /> Arşiv dahil</label>
          <button class="secondary-btn" id="applySessionFiltersBtn">Ara</button>
          <button class="secondary-btn" id="clearSessionFiltersBtn">Temizle</button>
        </div>
        <div class="session-list">${recentHtml}</div>
      </div>
    </section>
  `;
  document.querySelectorAll("[data-go]").forEach((button) => {
    button.onclick = () => setScreen(button.dataset.go);
  });
  document.querySelector("#refreshSessionsBtn").onclick = refreshSessions;
  document.querySelector("#applySessionFiltersBtn").onclick = applySessionFilters;
  document.querySelector("#clearSessionFiltersBtn").onclick = clearSessionFilters;
  document.querySelector("#sessionSearchInput").onkeydown = (event) => {
    if (event.key === "Enter") applySessionFilters();
  };
  document.querySelectorAll("[data-session-open]").forEach((button) => {
    button.onclick = () => openSession(button.dataset.sessionOpen, "voice");
  });
  document.querySelectorAll("[data-session-archive]").forEach((button) => {
    button.onclick = () => archiveSession(button.dataset.sessionArchive);
  });
  document.querySelectorAll("[data-session-restore]").forEach((button) => {
    button.onclick = () => restoreSession(button.dataset.sessionRestore);
  });
  document.querySelectorAll("[data-session-delete]").forEach((button) => {
    button.onclick = () => deleteSession(button.dataset.sessionDelete);
  });
}

async function applySessionFilters() {
  state.sessionFilters.query = document.querySelector("#sessionSearchInput").value.trim();
  state.sessionFilters.status = document.querySelector("#sessionStatusFilter").value;
  state.sessionFilters.includeArchived = document.querySelector("#includeArchivedInput").checked;
  await refreshSessions("filtre uygulandı");
}

async function clearSessionFilters() {
  state.sessionFilters = { query: "", status: "", includeArchived: false };
  await refreshSessions("filtre temizlendi");
}

async function refreshSessions(message = "oturum listesi yenilendi") {
  await loadSessions();
  updateStatus(message);
  renderHome();
}

async function archiveSession(sessionId) {
  await api(`/api/sessions/${sessionId}/archive`, { method: "POST" });
  if (state.session?.id === sessionId) state.session.archived = true;
  await refreshSessions("oturum arşivlendi");
}

async function restoreSession(sessionId) {
  const session = await api(`/api/sessions/${sessionId}/restore`, { method: "POST" });
  if (state.session?.id === sessionId) state.session = session;
  await refreshSessions("oturum geri alındı");
}

async function deleteSession(sessionId) {
  const ok = window.confirm("Bu oturumu kalıcı olarak silmek istediğinize emin misiniz?");
  if (!ok) return;
  await api(`/api/sessions/${sessionId}`, { method: "DELETE" });
  await loadSessions();
  if (state.session?.id === sessionId) {
    state.session = state.sessions[0] || null;
    state.reportPreview = "";
  }
  if (!state.session) await createSession();
  else {
    updateStatus("oturum silindi");
    renderHome();
  }
}

function renderSessionCard(session) {
  const patient = session.patient || {};
  const name = patient.displayName || "Yeni hasta";
  const complaint = patient.chiefComplaint || "Ana şikayet yok";
  const updated = formatDateTime(session.updatedAt || session.createdAt);
  const active = state.session?.id === session.id;
  const status = session.archived ? "Arşiv" : session.finalized ? "Final" : session.summary ? "Özetli" : session.transcript ? "Transkript" : "Taslak";
  return `
    <article class="session-card ${active ? "selected" : ""} ${session.archived ? "archived" : ""}">
      <button class="session-open" data-session-open="${escapeHtml(session.id)}">
        <strong>${escapeHtml(name)}</strong>
        <span>${escapeHtml(complaint)}</span>
      </button>
      <div class="session-meta">
        <small>${escapeHtml(updated)}</small>
        <em>${escapeHtml(status)}</em>
      </div>
      <div class="session-actions">
        ${session.archived
          ? `<button class="mini-btn" data-session-restore="${escapeHtml(session.id)}">Geri al</button>`
          : `<button class="mini-btn" data-session-archive="${escapeHtml(session.id)}">Arşivle</button>`}
        <button class="mini-btn danger-mini" data-session-delete="${escapeHtml(session.id)}">Sil</button>
      </div>
    </article>
  `;
}

function formatDateTime(value) {
  if (!value) return "Tarih yok";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("tr-TR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function moduleHeader(title, subtitle = "") {
  return `
    <div class="module-header">
      <div>
        <h1>${escapeHtml(title)}</h1>
        ${subtitle ? `<p class="muted">${escapeHtml(subtitle)}</p>` : ""}
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
  const patient = state.session?.patient || {};
  content.innerHTML = `
    <section class="screen patientsum-screen">
      <div class="panel patient-card">
        ${moduleHeader("PatientSum", "Hasta bilgisi, ses kaydı, transkript, özet ve hekim onayı.")}
        <div class="field-grid patient-grid">
          <div class="field">
            <label for="patientName">Hasta adı / kısa tanım</label>
            <input id="patientName" value="${escapeHtml(patient.displayName || "")}" placeholder="Yeni hasta" />
          </div>
          <div class="field">
            <label for="patientAge">Yaş</label>
            <input id="patientAge" value="${escapeHtml(patient.age || "")}" inputmode="numeric" placeholder="Örn. 42" />
          </div>
          <div class="field">
            <label for="patientSex">Cinsiyet</label>
            <select id="patientSex">
              <option value="" ${!patient.sex ? "selected" : ""}>Belirtilmedi</option>
              <option value="Kadın" ${patient.sex === "Kadın" ? "selected" : ""}>Kadın</option>
              <option value="Erkek" ${patient.sex === "Erkek" ? "selected" : ""}>Erkek</option>
              <option value="Diğer/Belirtmek istemiyor" ${patient.sex === "Diğer/Belirtmek istemiyor" ? "selected" : ""}>Diğer/Belirtmek istemiyor</option>
            </select>
          </div>
          <div class="field">
            <label for="chiefComplaint">Ana şikayet</label>
            <input id="chiefComplaint" value="${escapeHtml(patient.chiefComplaint || "")}" placeholder="Örn. diz ağrısı" />
          </div>
        </div>
        <div class="actions">
          <button class="secondary-btn" id="savePatientBtn">Hasta Bilgisini Kaydet</button>
          <button class="primary-btn" id="startRecordBtn">
            <span class="recording-dot ${voice.recording ? "on" : ""}"></span>Kaydı Başlat
          </button>
          <button class="danger-btn" id="stopRecordBtn" ${voice.recording ? "" : "disabled"}>Durdur ve Transkripte Dök</button>
          <button class="secondary-btn" id="summaryBtn">Özet Oluştur</button>
        </div>
        <p class="muted" id="voiceStatus">${voice.recording ? "Kayıt devam ediyor." : "Kayıt, transkript veya manuel not ile özet oluşturabilirsiniz."}</p>
        <div class="field">
          <label for="transcriptText">Transkript / Görüşme Notu</label>
          <textarea id="transcriptText" placeholder="Ses kaydı yerine notu buraya yazabilir veya yapıştırabilirsiniz.">${escapeHtml(state.session?.transcript || "")}</textarea>
        </div>
      </div>
      <div class="panel doctor-card">
        <div class="module-header compact-header">
          <div>
            <h1>Özet ve Hekim Notu</h1>
            <p class="muted">Final rapordan önce hekim kontrolü gerekir.</p>
          </div>
          <span class="final-badge ${state.session?.finalized ? "done" : ""}">${state.session?.finalized ? "Final" : "Taslak"}</span>
        </div>
        <h2>AI / Klinik Özet</h2>
        <div class="result summary-result">${escapeHtml(state.session?.summary || "Henüz özet yok.")}</div>
        <div class="field">
          <label for="doctorNotesText">Hekim Notu</label>
          <textarea id="doctorNotesText" placeholder="Muayene, karar, plan veya düzenleme notu girin.">${escapeHtml(state.session?.doctorNotes || "")}</textarea>
        </div>
        <div class="field">
          <label for="warningsText">Uyarılar / Red flag notları</label>
          <textarea id="warningsText" placeholder="Her satıra bir uyarı yazabilirsiniz.">${escapeHtml((state.session?.warnings || []).join("\n"))}</textarea>
        </div>
        <div class="actions">
          <button class="secondary-btn" id="saveClinicalBtn">Hekim Notunu Kaydet</button>
          <button class="primary-btn" id="reportPreviewBtn">Rapor Önizle</button>
          <button class="secondary-btn" id="openHtmlReportBtn">HTML Raporu Aç</button>
          <button class="secondary-btn" id="downloadTxtReportBtn">TXT İndir</button>
          <button class="danger-btn" id="finalizeBtn">${state.session?.finalized ? "Finali Geri Al" : "Final Onayla"}</button>
        </div>
        <div class="result report-result">${escapeHtml(state.reportPreview || "Rapor önizleme henüz oluşturulmadı.")}</div>
      </div>
    </section>
  `;
  bindBackButton();
  document.querySelector("#savePatientBtn").onclick = savePatientInfo;
  document.querySelector("#startRecordBtn").onclick = startRecording;
  document.querySelector("#stopRecordBtn").onclick = stopAndTranscribe;
  document.querySelector("#summaryBtn").onclick = summarizeTranscript;
  document.querySelector("#saveClinicalBtn").onclick = saveClinicalNotes;
  document.querySelector("#reportPreviewBtn").onclick = loadReportPreview;
  document.querySelector("#openHtmlReportBtn").onclick = openHtmlReport;
  document.querySelector("#downloadTxtReportBtn").onclick = downloadTxtReport;
  document.querySelector("#finalizeBtn").onclick = toggleFinalize;
}

async function savePatientInfo() {
  const patient = {
    displayName: document.querySelector("#patientName").value.trim() || "Yeni hasta",
    age: document.querySelector("#patientAge").value.trim(),
    sex: document.querySelector("#patientSex").value,
    chiefComplaint: document.querySelector("#chiefComplaint").value.trim(),
  };
  state.session = await api(`/api/sessions/${state.session.id}`, {
    method: "PATCH",
    body: JSON.stringify({ patient }),
  });
  await loadSessions();
  updateStatus("hasta bilgisi kaydedildi");
  renderVoice();
}

async function saveClinicalNotes() {
  const doctorNotes = document.querySelector("#doctorNotesText").value;
  const warnings = document
    .querySelector("#warningsText")
    .value.split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  state.session = await api(`/api/sessions/${state.session.id}`, {
    method: "PATCH",
    body: JSON.stringify({ doctorNotes, warnings }),
  });
  await loadSessions();
  updateStatus("hekim notu kaydedildi");
  renderVoice();
}

async function toggleFinalize() {
  await saveClinicalNotes();
  state.session = await api(`/api/sessions/${state.session.id}`, {
    method: "PATCH",
    body: JSON.stringify({ finalized: !state.session.finalized }),
  });
  await loadSessions();
  updateStatus(state.session.finalized ? "final onaylandı" : "taslağa döndü");
  await loadReportPreview(false);
}

async function loadReportPreview(announce = true) {
  await saveClinicalNotes();
  const payload = await api(`/api/sessions/${state.session.id}/report-preview`);
  state.session = payload.session;
  state.reportPreview = payload.report;
  if (announce) updateStatus("rapor önizleme hazır");
  renderVoice();
}

async function openHtmlReport() {
  await saveClinicalNotes();
  window.open(`/api/sessions/${state.session.id}/report.html`, "_blank", "noopener,noreferrer");
  updateStatus("HTML rapor açıldı");
}

async function downloadTxtReport() {
  await saveClinicalNotes();
  window.location.href = `/api/sessions/${state.session.id}/report.txt`;
  updateStatus("TXT rapor indiriliyor");
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
  await loadSessions();
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
  await loadSessions();
}

async function summarizeTranscript() {
  await savePatientInfo();
  await saveTranscript();
  updateVoiceStatus("Özet oluşturuluyor...");
  const payload = await api(`/api/sessions/${state.session.id}/summary`, {
    method: "POST",
    body: JSON.stringify({ language: "tr" }),
  });
  state.session = payload.session;
  await loadSessions();
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
        .map((model) => `<option value="${escapeHtml(model.id)}">${model.exists ? "" : "[eksik] "}${escapeHtml(model.name)}</option>`)
        .join("");
      return `<optgroup label="${escapeHtml(domain)}">${options}</optgroup>`;
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
        <div class="result">${escapeHtml(lastImagingText())}</div>
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
  await loadSessions();
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
  const sessions = await loadSessions();
  if (sessions.length) {
    state.session = sessions[0];
    updateStatus("son oturum açıldı");
    renderHome();
  } else {
    await createSession();
  }
}

init().catch((error) => {
  statusText.textContent = "Hata";
  content.innerHTML = `<div class="panel"><h1>Başlatılamadı</h1><pre>${escapeHtml(String(error))}</pre></div>`;
});
