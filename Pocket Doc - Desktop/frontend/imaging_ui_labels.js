function clarifyImagingUiLabels() {
  const imageFile = document.querySelector("#imageFile");
  const analyzeBtn = document.querySelector("#analyzeBtn");
  const cameraBtn = document.querySelector("#cameraPlaceholderBtn");
  if (!imageFile || !analyzeBtn) return;

  const panel = imageFile.closest(".panel");
  if (panel) {
    const mutedParagraphs = Array.from(panel.querySelectorAll("p.muted"));
    mutedParagraphs.forEach((paragraph) => {
      if (paragraph.textContent.includes("mock analiz")) {
        paragraph.textContent = "Dosya yükleme gerçek Ultralytics inference backend'i ile çalışır. Kamera canlı görüntüsü ayrı modül olarak daha sonra eklenecek.";
      }
    });
  }

  analyzeBtn.textContent = "Dosyayı Analiz Et";

  if (cameraBtn && !cameraBtn.dataset.clarified) {
    cameraBtn.dataset.clarified = "true";
    cameraBtn.textContent = "Kamera Modülü Yakında";
    cameraBtn.onclick = () => {
      if (typeof updateStatus === "function") {
        updateStatus("kamera canlı görüntüsü henüz aktif değil; dosya yükleyip Dosyayı Analiz Et butonunu kullanın");
      }
      window.alert("Kamera canlı görüntüsü henüz aktif değil. Gerçek model analizi için lütfen bir görüntü dosyası yükleyip 'Dosyayı Analiz Et' butonunu kullanın.");
    };
  }
}

const imagingUiLabelsObserver = new MutationObserver(() => clarifyImagingUiLabels());
imagingUiLabelsObserver.observe(document.documentElement, { childList: true, subtree: true });
document.addEventListener("DOMContentLoaded", clarifyImagingUiLabels);
