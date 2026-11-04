"use strict";
const $ = id => document.getElementById(id);

let PAGE_ELS = [];
let RENDER = async () => {};

/* ---------- high-quality, lazy rendering of the real exam.pdf ---------- */
async function setupPdf() {
  const host = $("pages");
  try {
    pdfjsLib.GlobalWorkerOptions.workerSrc =
      "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

    const pdf = await pdfjsLib.getDocument("exam.pdf?v=8").promise;
    const dpr = window.devicePixelRatio || 1;
    // oversample: ~2x on standard screens, up to 3x on retina → crisp text & thin grid
    const QUALITY = Math.min(Math.max(dpr, 1) + 1, 3);
    const MAX_SIDE = 4200; // cap any single canvas dimension (memory safety)

    // 1) lay out all pages as aspect-correct placeholders
    for (let n = 1; n <= pdf.numPages; n++) {
      const page = await pdf.getPage(n);
      const base = page.getViewport({ scale: 1 });
      const wrap = document.createElement("div");
      wrap.className = "pdf-page";
      wrap.style.aspectRatio = base.width + " / " + base.height;
      wrap.setAttribute("aria-label", "עמוד " + n);
      wrap._page = page;
      wrap._base = base;


      host.append(wrap);
      PAGE_ELS.push(wrap);
    }
    $("loading").hidden = true;

    // 2) render one page at high resolution
    RENDER = async function (wrap) {
      if (wrap._done || wrap._busy) return;
      wrap._busy = true;
      const { _page: page, _base: base } = wrap;
      const cssW = wrap.clientWidth || Math.min(host.clientWidth || 794, 794);
      let scale = (cssW / base.width) * QUALITY;
      let vp = page.getViewport({ scale });
      const big = Math.max(vp.width, vp.height);
      if (big > MAX_SIDE) { scale *= MAX_SIDE / big; vp = page.getViewport({ scale }); }

      const canvas = document.createElement("canvas");
      canvas.width = Math.floor(vp.width);
      canvas.height = Math.floor(vp.height);
      const ctx = canvas.getContext("2d", { alpha: false });
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = "high";
      await page.render({ canvasContext: ctx, viewport: vp }).promise;
      wrap.replaceChildren(canvas);
      wrap._renderedAt = cssW;
      wrap._done = true;
      wrap._busy = false;
    };

    // 3) render lazily as pages approach the viewport
    const io = new IntersectionObserver(
      entries => { for (const e of entries) if (e.isIntersecting) RENDER(e.target); },
      { root: null, rootMargin: "1400px 0px", threshold: 0 }
    );
    PAGE_ELS.forEach(el => io.observe(el));

    // 4) re-render crisp after a meaningful width change (e.g. rotate / resize)
    let rt;
    window.addEventListener("resize", () => {
      clearTimeout(rt);
      rt = setTimeout(() => {
        for (const el of PAGE_ELS) {
          if (el._done && Math.abs((el.clientWidth || 0) - (el._renderedAt || 0)) > 40) {
            el._done = false;
            if (el.getBoundingClientRect().top < window.innerHeight * 2) RENDER(el);
          }
        }
      }, 350);
    });
  } catch (err) {
    console.error(err);
    $("loading").innerHTML =
      'לא ניתן להציג את עמודי המבחן כעת. ' +
      '<a href="exam.pdf?v=8" style="color:#0e8f80;font-weight:800">פתחו את ה-PDF ישירות</a>.';
  }
}

/* ---------- thin reading-progress bar under the top bar ---------- */
function wireProgress() {
  const fill = $("scroll-fill");
  if (!fill) return;
  const onScroll = () => {
    const h = document.documentElement;
    const max = h.scrollHeight - h.clientHeight;
    fill.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
  };
  document.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
}

wireProgress();
setupPdf();
