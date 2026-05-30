const demoInferenceState = {
  conf: 0.25,
  iou: 0.45,
  imgsz: 640,
  max_det: 300,
};

function loadDemoDefaults() {
  try {
    const defaults = state?.health?.demoInferenceDefaults;
    if (!defaults) return;
    demoInferenceState.conf = Number(defaults.conf ?? demoInferenceState.conf);
    demoInferenceState.iou = Number(defaults.iou ?? demoInferenceState.iou);
    demoInferenceState.imgsz = Number(defaults.imgsz ?? demoInferenceState.imgsz);
    demoInferenceState.max_det = Number(defaults.max_det ?? demoInferenceState.max_det);
  } catch {
    // Keep local defaults.
  }
}

function ensureDemoInferenceControls() {
  const modelSelect = document.querySelector("#modelSelect");
  const imageFile = document.querySelector("#imageFile");
  const imagingScreen = modelSelect?.closest(".screen");
  if (!modelSelect || !imageFile || !imagingScreen) return;
  loadDemoDefaults();

  if (!document.querySelector("#demoInferencePanel")) {
    const panel = document.createElement("div");
    panel.className = "panel demo-inference-panel";
    panel.id = "demoInferencePanel";
    panel.innerHTML = `
      <h2>Demo Inference Ayarları</h2>
      <p class="muted">Yüklediğiniz demo .py dosyasındaki Ultralytics predict parametreleriyle aynı mantıkta çalışır.</p>
      <div class="field-grid demo-inference-grid">
        <div class="field">
          <label for="demoConfInput">Confidence Threshold</label>
          <input id="demoConfInput" type="number" min="0.05" max="0.95" step="0.01" value="${demoInferenceState.conf}" />
        </div>
        <div class="field">
          <label for="demoIouInput">IoU (NMS)</label>
          <input id="demoIouInput" type="number" min="0.10" max="0.95" step="0.01" value="${demoInferenceState.iou}" />
        </div>
        <div class="field">
          <label for="demoImgszInput">Image Size</label>
          <select id="demoImgszInput">${[320, 416, 512, 640, 768, 896, 1024].map((v) => `<option value="${v}" ${Number(demoInferenceState.imgsz) === v ? "selected" : ""}>${v}</option>`).join("")}</select>
        </div>
        <div class="field">
          <label for="demoMaxDetInput">Max Det</label>
          <select id="demoMaxDetInput">${[50, 100, 200, 300, 500, 1000].map((v) => `<option value="${v}" ${Number(demoInferenceState.max_det) === v ? "selected" : ""}>${v}</option>`).join("")}</select>
        </div>
      </div>
    `;
    const firstPanel = imagingScreen.querySelector(".panel");
    if (firstPanel) firstPanel.after(panel);
    else imagingScreen.prepend(panel);
    bindDemoInferenceInputs();
  }
}

function bindDemoInferenceInputs() {
  const conf = document.querySelector("#demoConfInput");
  const iou = document.querySelector("#demoIouInput");
  const imgsz = document.querySelector("#demoImgszInput");
  const maxDet = document.querySelector("#demoMaxDetInput");
  if (conf) conf.oninput = () => demoInferenceState.conf = clampNumber(conf.value, 0.05, 0.95, 0.25);
  if (iou) iou.oninput = () => demoInferenceState.iou = clampNumber(iou.value, 0.10, 0.95, 0.45);
  if (imgsz) imgsz.onchange = () => demoInferenceState.imgsz = Number(imgsz.value || 640);
  if (maxDet) maxDet.onchange = () => demoInferenceState.max_det = Number(maxDet.value || 300);
}

function clampNumber(value, min, max, fallback) {
  const number = Number(value);
  if (!Number.isFinite(number)) return fallback;
  return Math.min(max, Math.max(min, number));
}

function getDemoInferenceOptions() {
  bindDemoInferenceInputs();
  return {
    conf: demoInferenceState.conf,
    iou: demoInferenceState.iou,
    imgsz: demoInferenceState.imgsz,
    max_det: demoInferenceState.max_det,
  };
}

function patchAnalyzeImageForDemoControls() {
  if (typeof analyzeImage !== "function" || analyzeImage.__demoControlsPatched) return;
  analyzeImage = async function analyzeImageWithDemoControls() {
    const file = document.querySelector("#imageFile")?.files?.[0];
    if (!file) {
      updateStatus("dosya seçilmedi");
      return;
    }
    const options = getDemoInferenceOptions();
    const form = new FormData();
    form.append("file", file);
    form.append("conf", String(options.conf));
    form.append("iou", String(options.iou));
    form.append("imgsz", String(options.imgsz));
    form.append("max_det", String(options.max_det));
    updateStatus(`analiz çalışıyor conf=${options.conf.toFixed(2)}, iou=${options.iou.toFixed(2)}, imgsz=${options.imgsz}, max_det=${options.max_det}`);
    const response = await fetch(`/api/sessions/${state.session.id}/imaging/${state.selectedModelId}`, {
      method: "POST",
      headers: secureHeaders(),
      body: form,
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(JSON.stringify(payload));
    state.session = payload.session;
    await loadSessions();
    updateStatus("görüntü analizi tamamlandı");
    render();
  };
  analyzeImage.__demoControlsPatched = true;
}

const demoInferenceObserver = new MutationObserver(() => {
  patchAnalyzeImageForDemoControls();
  ensureDemoInferenceControls();
});
demoInferenceObserver.observe(document.documentElement, { childList: true, subtree: true });
document.addEventListener("DOMContentLoaded", () => {
  patchAnalyzeImageForDemoControls();
  ensureDemoInferenceControls();
});
