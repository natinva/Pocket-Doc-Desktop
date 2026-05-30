function ensureModelMetadataPanel() {
  const modelSelect = document.querySelector("#modelSelect");
  const imagingScreen = modelSelect?.closest(".screen");
  if (!modelSelect || !imagingScreen) return;

  if (!modelSelect.dataset.metadataBound) {
    modelSelect.dataset.metadataBound = "true";
    modelSelect.addEventListener("change", renderSelectedModelMetadata);
  }

  if (!document.querySelector("#modelMetadataPanel")) {
    const panel = document.createElement("div");
    panel.className = "panel model-metadata-panel";
    panel.id = "modelMetadataPanel";
    panel.innerHTML = `<h2>Model Bilgisi</h2><div class="result" id="modelMetadataResult">Model seçildiğinde bilgiler burada görünecek.</div>`;
    const firstPanel = imagingScreen.querySelector(".panel");
    if (firstPanel) firstPanel.after(panel);
    else imagingScreen.prepend(panel);
  }

  renderSelectedModelMetadata();
}

function renderSelectedModelMetadata() {
  const modelSelect = document.querySelector("#modelSelect");
  const result = document.querySelector("#modelMetadataResult");
  if (!modelSelect || !result || typeof state === "undefined") return;
  const model = (state.models || []).find((item) => item.id === modelSelect.value);
  if (!model) {
    result.textContent = "Model bilgisi bulunamadı.";
    return;
  }
  const outputs = (model.outputTypes || []).join(", ") || "-";
  const postprocess = model.postprocess || "Yok";
  const parser = model.requiresCustomParser ? "Gerekebilir" : "Standart adapter";
  result.innerHTML = `
    <div class="metric-row"><span>Görev tipi</span><strong>${escapeHtml(model.taskType || "-")}</strong></div>
    <div class="metric-row"><span>Çıktılar</span><strong>${escapeHtml(outputs)}</strong></div>
    <div class="metric-row"><span>Model dosyası</span><strong>${model.exists ? "Bulundu" : "Eksik"}</strong></div>
    <div class="metric-row"><span>Uzantı</span><strong>${escapeHtml(model.extension || "-")}</strong></div>
    <div class="metric-row"><span>Parser</span><strong>${escapeHtml(parser)}</strong></div>
    <div class="metric-row"><span>Postprocess</span><strong>${escapeHtml(postprocess)}</strong></div>
    <p><strong>Klinik kullanım:</strong> ${escapeHtml(model.clinicalUseTR || "-")}</p>
    <p><strong>Girdi gereksinimi:</strong> ${escapeHtml(model.inputRequirementsTR || "-")}</p>
    <p><strong>Güvenlik notu:</strong> ${escapeHtml(model.safetyNoteTR || "-")}</p>
  `;
}

const modelMetadataObserver = new MutationObserver(() => ensureModelMetadataPanel());
modelMetadataObserver.observe(document.documentElement, { childList: true, subtree: true });
document.addEventListener("DOMContentLoaded", ensureModelMetadataPanel);
