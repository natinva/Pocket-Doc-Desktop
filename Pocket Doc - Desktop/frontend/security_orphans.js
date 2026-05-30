function formatBytes(bytes) {
  const value = Number(bytes || 0);
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function orphanHeaders(extra = {}) {
  return typeof secureHeaders === "function" ? secureHeaders(extra) : extra;
}

async function orphanApi(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...orphanHeaders(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json();
}

function ensureOrphanPanel() {
  const screen = document.querySelector(".security-screen");
  if (!screen || document.querySelector("#orphanPanel")) return;
  const panel = document.createElement("div");
  panel.className = "panel";
  panel.id = "orphanPanel";
  panel.innerHTML = `
    <h2>Yetim Upload Dosyaları</h2>
    <p class="muted">Oturumlara bağlı olmayan eski ses/görüntü dosyalarını tarar. Silme işlemi sadece uploads klasörü içinde yapılır.</p>
    <div class="security-grid">
      <div class="metric-row"><span>Yetim dosya</span><strong id="orphanCount">-</strong></div>
      <div class="metric-row"><span>Toplam boyut</span><strong id="orphanBytes">-</strong></div>
    </div>
    <div class="actions">
      <button class="secondary-btn" id="scanOrphansBtn">Yetim Dosyaları Tara</button>
      <button class="danger-btn" id="cleanupOrphansBtn">Yetim Dosyaları Temizle</button>
    </div>
    <div class="result" id="orphanResult">Henüz tarama yapılmadı.</div>
  `;
  const auditPanel = screen.querySelector(".audit-panel");
  screen.insertBefore(panel, auditPanel || null);
  document.querySelector("#scanOrphansBtn").onclick = scanOrphans;
  document.querySelector("#cleanupOrphansBtn").onclick = cleanupOrphans;
  if (typeof state !== "undefined" && state.securityOverview?.orphanFiles) {
    renderOrphanResult(state.securityOverview.orphanFiles, false);
  }
}

function renderOrphanResult(payload, detailed = true) {
  const count = Number(payload.orphanCount || 0);
  const bytes = Number(payload.orphanBytes || 0);
  const countEl = document.querySelector("#orphanCount");
  const bytesEl = document.querySelector("#orphanBytes");
  const resultEl = document.querySelector("#orphanResult");
  if (countEl) countEl.textContent = String(count);
  if (bytesEl) bytesEl.textContent = formatBytes(bytes);
  if (!resultEl) return;
  const items = payload.items || [];
  const list = detailed && items.length
    ? `<ul>${items.slice(0, 20).map((item) => `<li>${escapeHtml(item.name || item.path)} — ${formatBytes(item.sizeBytes)}</li>`).join("")}</ul>`
    : "";
  resultEl.innerHTML = count
    ? `${count} yetim dosya bulundu (${formatBytes(bytes)}).${list}`
    : "Yetim upload dosyası bulunmadı.";
}

async function scanOrphans() {
  try {
    const payload = await orphanApi("/api/security/orphan-files");
    renderOrphanResult(payload, true);
    if (typeof updateStatus === "function") updateStatus("yetim dosya taraması tamamlandı");
  } catch (error) {
    const resultEl = document.querySelector("#orphanResult");
    if (resultEl) resultEl.textContent = `Tarama hatası: ${error.message || error}`;
  }
}

async function cleanupOrphans() {
  const ok = window.confirm("Oturumlara bağlı olmayan upload dosyaları silinsin mi? Bu işlem geri alınamaz.");
  if (!ok) return;
  try {
    const payload = await orphanApi("/api/security/orphan-files/cleanup", {
      method: "POST",
      body: JSON.stringify({ confirm: true }),
    });
    const resultEl = document.querySelector("#orphanResult");
    if (resultEl) resultEl.textContent = `${payload.deletedCount || 0} dosya temizlendi (${formatBytes(payload.deletedBytes)}).`;
    document.querySelector("#orphanCount").textContent = "0";
    document.querySelector("#orphanBytes").textContent = "0 B";
    if (typeof updateStatus === "function") updateStatus("yetim upload dosyaları temizlendi");
  } catch (error) {
    const resultEl = document.querySelector("#orphanResult");
    if (resultEl) resultEl.textContent = `Temizlik hatası: ${error.message || error}`;
  }
}

const orphanObserver = new MutationObserver(() => ensureOrphanPanel());
orphanObserver.observe(document.documentElement, { childList: true, subtree: true });
document.addEventListener("DOMContentLoaded", ensureOrphanPanel);
