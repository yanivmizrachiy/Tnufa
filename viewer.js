"use strict";
const $ = id => document.getElementById(id);

/* ---------- render the user's real exam.pdf, page by page ---------- */
async function renderPdf() {
  const host = $("pages");
  try {
    pdfjsLib.GlobalWorkerOptions.workerSrc =
      "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

    const pdf = await pdfjsLib.getDocument("exam.pdf").promise;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const cssW = Math.min(host.clientWidth || 794, 794);

    const frag = document.createDocumentFragment();
    for (let n = 1; n <= pdf.numPages; n++) {
      if (n > 1) {
        const sep = document.createElement("div");
        sep.className = "sep";
        sep.setAttribute("role", "separator");
        sep.setAttribute("aria-hidden", "true");
        frag.append(sep);
      }
      const page = await pdf.getPage(n);
      const base = page.getViewport({ scale: 1 });
      const scale = (cssW / base.width) * dpr;
      const vp = page.getViewport({ scale });

      const wrap = document.createElement("div");
      wrap.className = "pdf-page";
      wrap.setAttribute("aria-label", "עמוד " + n);
      const canvas = document.createElement("canvas");
      canvas.width = Math.floor(vp.width);
      canvas.height = Math.floor(vp.height);
      wrap.append(canvas);
      frag.append(wrap);

      await page.render({ canvasContext: canvas.getContext("2d"), viewport: vp }).promise;
    }
    host.append(frag);
    $("loading").hidden = true;
  } catch (err) {
    console.error(err);
    $("loading").innerHTML =
      'לא ניתן להציג את עמודי המבחן כעת. ' +
      '<a href="exam.pdf" style="color:#0e8f80;font-weight:800">פתחו את ה-PDF ישירות</a>.';
  }
}

/* ---------- chrome: print, scroll progress, back-to-top ---------- */
function wireChrome() {
  $("print-btn").addEventListener("click", () => window.print());
  const fill = $("scroll-fill");
  const toTop = $("to-top");
  const onScroll = () => {
    const h = document.documentElement;
    const max = h.scrollHeight - h.clientHeight;
    fill.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
    toTop.hidden = false;
    toTop.classList.toggle("show", h.scrollTop > 480);
  };
  document.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  toTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
}

wireChrome();
renderPdf();
