let pocketDocPreviewUrl = "";
let pocketDocPreviewName = "";

function ensureImagingOverlay() {
  const imageInput = document.querySelector("#imageFile");
  const imagingScreen = imageInput?.closest(".screen");
  if (!imageInput || !imagingScreen) return;

  if (!imageInput.dataset.overlayBound) {
    imageInput.dataset.overlayBound = "true";
    imageInput.addEventListener("change", () => {
      const file = imageInput.files?.[0];
      if (!file) return;
      if (pocketDocPreviewUrl) URL.revokeObjectURL(pocketDocPreviewUrl);
      pocketDocPreviewUrl = URL.createObjectURL(file);
      pocketDocPreviewName = file.name || "selected-image";
      renderImagingOverlay();
    });
  }

  if (!document.querySelector("#imagingOverlayPanel")) {
    const panel = document.createElement("div");
    panel.className = "panel imaging-overlay-panel";
    panel.id = "imagingOverlayPanel";
    panel.innerHTML = `
      <h2>Görüntü Önizleme ve Tespitler</h2>
      <p class="muted">Bounding box sonuçları seçilen lokal görüntünün üzerine çizilir. Eski oturumlarda ham görüntü tarayıcıda olmadığı için sadece metin sonucu gösterilebilir.</p>
      <div class="imaging-preview-wrap">
        <img id="imagingPreviewImage" alt="Görüntü önizleme" />
        <canvas id="imagingOverlayCanvas"></canvas>
      </div>
      <div class="result" id="imagingDetectionList">Henüz görüntü seçilmedi veya tespit sonucu yok.</div>
    `;
    imagingScreen.appendChild(panel);
  }

  renderImagingOverlay();
}

function renderImagingOverlay() {
  const panel = document.querySelector("#imagingOverlayPanel");
  const image = document.querySelector("#imagingPreviewImage");
  const canvas = document.querySelector("#imagingOverlayCanvas");
  const list = document.querySelector("#imagingDetectionList");
  if (!panel || !image || !canvas || !list) return;

  const result = getLastImagingResult();
  if (!pocketDocPreviewUrl) {
    image.removeAttribute("src");
    canvas.width = 0;
    canvas.height = 0;
    list.innerHTML = renderDetectionList(result, false);
    return;
  }

  if (image.src !== pocketDocPreviewUrl) {
    image.onload = () => drawDetections(result);
    image.src = pocketDocPreviewUrl;
  } else {
    drawDetections(result);
  }
  list.innerHTML = renderDetectionList(result, true);
}

function getLastImagingResult() {
  try {
    return state?.session?.imagingResults?.at(-1) || null;
  } catch {
    return null;
  }
}

function renderDetectionList(result, hasPreview) {
  if (!result) {
    return hasPreview
      ? `Seçilen görüntü: ${escapeHtml(pocketDocPreviewName)}. Analiz sonrası tespitler burada görünecek.`
      : "Henüz analiz sonucu yok.";
  }

  const detections = result.detections || [];
  const classifications = result.classifications || [];
  const warnings = result.warningsTR || [];
  const detectionRows = detections.length
    ? `<h3>Tespitler</h3><ol>${detections.map((item) => `<li><strong>${escapeHtml(item.label || "bulgu")}</strong> — güven: ${formatConfidence(item.confidence)} — bbox: ${escapeHtml((item.bboxXYXY || []).map((v) => Math.round(Number(v))).join(", "))}</li>`).join("")}</ol>`
    : "<p>Tespit kutusu yok.</p>";
  const classificationRows = classifications.length
    ? `<h3>Sınıflama</h3><ol>${classifications.map((item) => `<li><strong>${escapeHtml(item.label || "sınıf")}</strong> — güven: ${formatConfidence(item.confidence)}</li>`).join("")}</ol>`
    : "";
  const warningRows = warnings.length
    ? `<h3>Uyarılar</h3><ul>${warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`).join("")}</ul>`
    : "";
  return `<p><strong>${escapeHtml(result.modelName || "Model")}</strong>: ${escapeHtml(result.resultSummaryTR || "Sonuç yok.")}</p>${detectionRows}${classificationRows}${warningRows}`;
}

function drawDetections(result) {
  const image = document.querySelector("#imagingPreviewImage");
  const canvas = document.querySelector("#imagingOverlayCanvas");
  if (!image || !canvas || !image.complete || !image.naturalWidth) return;

  const rect = image.getBoundingClientRect();
  canvas.width = Math.round(rect.width);
  canvas.height = Math.round(rect.height);
  canvas.style.width = `${rect.width}px`;
  canvas.style.height = `${rect.height}px`;

  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const detections = result?.detections || [];
  if (!detections.length) return;

  const scaleX = canvas.width / image.naturalWidth;
  const scaleY = canvas.height / image.naturalHeight;
  ctx.lineWidth = 2;
  ctx.font = "13px Arial";

  detections.forEach((item, index) => {
    const [x1, y1, x2, y2] = (item.bboxXYXY || []).map(Number);
    if (![x1, y1, x2, y2].every(Number.isFinite)) return;
    const x = x1 * scaleX;
    const y = y1 * scaleY;
    const w = Math.max(0, (x2 - x1) * scaleX);
    const h = Math.max(0, (y2 - y1) * scaleY);
    ctx.strokeRect(x, y, w, h);
    const label = `${index + 1}. ${item.label || "bulgu"} ${formatConfidence(item.confidence)}`;
    const labelWidth = ctx.measureText(label).width + 8;
    const labelY = Math.max(18, y);
    ctx.fillRect(x, labelY - 16, labelWidth, 18);
    ctx.clearRect(x + 1, labelY - 15, labelWidth - 2, 16);
    ctx.fillText(label, x + 4, labelY - 3);
  });
}

function formatConfidence(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "-";
  return `%${Math.round(number * 1000) / 10}`;
}

function patchAnalyzeImageForOverlay() {
  if (typeof analyzeImage !== "function" || analyzeImage.__overlayPatched) return;
  const originalAnalyzeImage = analyzeImage;
  analyzeImage = async function patchedAnalyzeImage() {
    const input = document.querySelector("#imageFile");
    const file = input?.files?.[0];
    if (file) {
      if (pocketDocPreviewUrl) URL.revokeObjectURL(pocketDocPreviewUrl);
      pocketDocPreviewUrl = URL.createObjectURL(file);
      pocketDocPreviewName = file.name || "selected-image";
    }
    await originalAnalyzeImage();
    setTimeout(ensureImagingOverlay, 0);
  };
  analyzeImage.__overlayPatched = true;
}

const imagingOverlayObserver = new MutationObserver(() => {
  patchAnalyzeImageForOverlay();
  ensureImagingOverlay();
});
imagingOverlayObserver.observe(document.documentElement, { childList: true, subtree: true });
document.addEventListener("DOMContentLoaded", () => {
  patchAnalyzeImageForOverlay();
  ensureImagingOverlay();
});
window.addEventListener("resize", () => renderImagingOverlay());
