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
      <p class="muted">BBox, segmentasyon polygon ve keypoint sonuçları seçilen lokal görüntünün üzerine çizilir. Eski oturumlarda ham görüntü tarayıcıda olmadığı için sadece metin sonucu gösterilebilir.</p>
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
    image.onload = () => drawOverlay(result);
    image.src = pocketDocPreviewUrl;
  } else {
    drawOverlay(result);
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
  const masks = result.masks || [];
  const keypoints = result.keypoints || [];
  const warnings = result.warningsTR || [];
  const detectionRows = detections.length
    ? `<h3>BBox Tespitleri</h3><ol>${detections.map((item) => `<li><strong>${escapeHtml(item.label || "bulgu")}</strong> — güven: ${formatConfidence(item.confidence)} — bbox: ${escapeHtml((item.bboxXYXY || []).map((v) => Math.round(Number(v))).join(", "))}</li>`).join("")}</ol>`
    : "<p>BBox tespiti yok.</p>";
  const maskRows = masks.length
    ? `<h3>Segmentasyon Maskeleri</h3><ol>${masks.map((item) => `<li><strong>${escapeHtml(item.label || "maske")}</strong> — güven: ${formatConfidence(item.confidence)} — nokta: ${(item.polygonXY || []).length}</li>`).join("")}</ol>`
    : "";
  const keypointRows = keypoints.length
    ? `<h3>Keypoint Grupları</h3><ol>${keypoints.map((item) => `<li><strong>${escapeHtml(item.label || "keypoint")}</strong> — nokta: ${(item.points || []).length}</li>`).join("")}</ol>`
    : "";
  const classificationRows = classifications.length
    ? `<h3>Sınıflama</h3><ol>${classifications.map((item) => `<li><strong>${escapeHtml(item.label || "sınıf")}</strong> — güven: ${formatConfidence(item.confidence)}</li>`).join("")}</ol>`
    : "";
  const warningRows = warnings.length
    ? `<h3>Uyarılar</h3><ul>${warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`).join("")}</ul>`
    : "";
  return `<p><strong>${escapeHtml(result.modelName || "Model")}</strong>: ${escapeHtml(result.resultSummaryTR || "Sonuç yok.")}</p>${detectionRows}${maskRows}${keypointRows}${classificationRows}${warningRows}`;
}

function drawOverlay(result) {
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

  const scaleX = canvas.width / image.naturalWidth;
  const scaleY = canvas.height / image.naturalHeight;
  ctx.lineWidth = 2;
  ctx.font = "13px Arial";

  drawMasks(ctx, result?.masks || [], scaleX, scaleY);
  drawDetections(ctx, result?.detections || [], scaleX, scaleY);
  drawKeypoints(ctx, result?.keypoints || [], scaleX, scaleY);
}

function drawDetections(ctx, detections, scaleX, scaleY) {
  detections.forEach((item, index) => {
    const [x1, y1, x2, y2] = (item.bboxXYXY || []).map(Number);
    if (![x1, y1, x2, y2].every(Number.isFinite)) return;
    const x = x1 * scaleX;
    const y = y1 * scaleY;
    const w = Math.max(0, (x2 - x1) * scaleX);
    const h = Math.max(0, (y2 - y1) * scaleY);
    ctx.strokeRect(x, y, w, h);
    const label = `${index + 1}. ${item.label || "bulgu"} ${formatConfidence(item.confidence)}`;
    drawCanvasLabel(ctx, label, x, Math.max(18, y));
  });
}

function drawMasks(ctx, masks, scaleX, scaleY) {
  masks.forEach((item, index) => {
    const points = item.polygonXY || [];
    if (points.length < 3) return;
    ctx.beginPath();
    points.forEach((point, pointIndex) => {
      const [rawX, rawY] = point.map(Number);
      if (!Number.isFinite(rawX) || !Number.isFinite(rawY)) return;
      const x = rawX * scaleX;
      const y = rawY * scaleY;
      if (pointIndex === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.globalAlpha = 0.18;
    ctx.fill();
    ctx.globalAlpha = 1;
    ctx.stroke();
    const [labelX, labelY] = points[0].map(Number);
    drawCanvasLabel(ctx, `${index + 1}. ${item.label || "maske"}`, labelX * scaleX, Math.max(18, labelY * scaleY));
  });
}

function drawKeypoints(ctx, groups, scaleX, scaleY) {
  groups.forEach((group, groupIndex) => {
    const points = group.points || [];
    points.forEach((point) => {
      const x = Number(point.x) * scaleX;
      const y = Number(point.y) * scaleY;
      if (!Number.isFinite(x) || !Number.isFinite(y)) return;
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.fillText(String(point.index ?? ""), x + 4, y - 4);
    });
    const first = points.find((point) => Number.isFinite(Number(point.x)) && Number.isFinite(Number(point.y)));
    if (first) drawCanvasLabel(ctx, `${groupIndex + 1}. ${group.label || "keypoints"}`, Number(first.x) * scaleX, Math.max(18, Number(first.y) * scaleY));
  });
}

function drawCanvasLabel(ctx, label, x, labelY) {
  const labelWidth = ctx.measureText(label).width + 8;
  ctx.fillRect(x, labelY - 16, labelWidth, 18);
  ctx.clearRect(x + 1, labelY - 15, labelWidth - 2, 16);
  ctx.fillText(label, x + 4, labelY - 3);
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
