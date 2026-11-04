"use strict";
/* Booklet viewer and phone app: renders exam.pdf page by page, joined by a glowing line.
   Scrolling stays native. Rendering is virtualized and sized to each device, so older phones stay smooth. */
(function () {
  const $ = id => document.getElementById(id);
  const PDF_URL = $("pdf-btn").getAttribute("href");
  const FILE_NAME = "מבחן-לקראת-תנופה.pdf";
  const TITLE = "לקראת תנופה: מבחן במתמטיקה לכיתה ט׳";
  const LAST_KEY = "tnufa-last-page";
  const INSTALL_KEY = "tnufa-install-offered";
  const MAX_ZOOM = 2;

  const isCoarse = window.matchMedia("(pointer: coarse)").matches;
  const isLowMemory = (navigator.deviceMemory || 4) <= 2;
  // Keeps every canvas under the iOS limit of 16.7 megapixels, and lower on small devices.
  const MAX_PIXELS = isLowMemory ? 4e6 : 12e6;
  const isIOS = /iP(hone|ad|od)/.test(navigator.userAgent) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  const isStandalone = () => window.matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
  const reducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private mode */ } },
  };

  const state = { pages: [], current: 0, zoom: 1, blob: null, installEvent: null, active: 0, queue: [] };

  /* ---------- toast ---------- */
  let toastTimer;
  function toast(text, action, ms) {
    const el = $("toast");
    el.textContent = "";
    el.append(Object.assign(document.createElement("span"), { textContent: text }));
    if (action) {
      const b = Object.assign(document.createElement("button"), { type: "button", textContent: action.label });
      b.addEventListener("click", () => { el.hidden = true; action.run(); });
      el.append(b);
    }
    el.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { el.hidden = true; }, ms || 3200);
  }

  /* ---------- loading the file once: it also serves the download and offline use ---------- */
  async function loadBytes() {
    const res = await fetch(PDF_URL);
    if (!res.ok) throw new Error("exam.pdf HTTP " + res.status);
    const total = Number(res.headers.get("content-length")) || 0;
    if (!res.body || !total) return new Uint8Array(await res.arrayBuffer());
    const reader = res.body.getReader();
    const out = new Uint8Array(total);
    let got = 0;
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      if (got + value.length > total) return new Uint8Array(await (await fetch(PDF_URL)).arrayBuffer());
      out.set(value, got);
      got += value.length;
      $("loading").textContent = "טוען את החוברת… " + Math.round((got / total) * 100) + "%";
    }
    return got === total ? out : out.slice(0, got);
  }

  /* ---------- rendering: nearest page first, at most two at a time ---------- */
  function targetWidth(p) {
    const css = p.el.clientWidth || 794;
    const pinch = window.visualViewport ? Math.max(1, window.visualViewport.scale) : 1;
    const wanted = css * Math.max((window.devicePixelRatio || 1) * 1.25, 2) * pinch;
    const aspect = p.base.height / p.base.width;
    return Math.floor(Math.min(wanted, Math.sqrt(MAX_PIXELS / aspect)));
  }

  function needsRender(p) {
    if (!p.wanted) return false;
    if (!p.canvas) return true;
    const t = targetWidth(p);
    return Math.abs(t - p.renderedWidth) / t > 0.15;
  }

  function schedule(p) {
    if (state.queue.indexOf(p) < 0 && !p.task) state.queue.push(p);
    pump();
  }

  function pump() {
    while (state.active < 2 && state.queue.length) {
      const here = state.current || 1;
      state.queue.sort((a, b) => Math.abs(a.n - here) - Math.abs(b.n - here));
      const p = state.queue.shift();
      if (needsRender(p)) renderPage(p);
    }
  }

  async function renderPage(p) {
    state.active++;
    try {
      const width = targetWidth(p);
      const vp = p.page.getViewport({ scale: width / p.base.width });
      const canvas = document.createElement("canvas");
      canvas.width = Math.floor(vp.width);
      canvas.height = Math.floor(vp.height);
      canvas.setAttribute("aria-hidden", "true");
      p.task = p.page.render({ canvasContext: canvas.getContext("2d", { alpha: false }), viewport: vp });
      await p.task.promise;
      p.task = null;
      if (p.wanted) {
        if (p.canvas) { p.canvas.replaceWith(canvas); p.canvas.width = 0; }
        else p.el.append(canvas);
        p.canvas = canvas;
        p.renderedWidth = width;
        p.el.classList.add("ready");
      } else {
        canvas.width = 0;
      }
    } catch (err) {
      p.task = null;
      if (!err || err.name !== "RenderingCancelledException") console.error(err);
    } finally {
      state.active--;
      pump();
    }
  }

  function freePage(p) {
    p.wanted = false;
    if (p.task) p.task.cancel();
    if (p.canvas) {
      p.canvas.remove();
      p.canvas.width = 0;
      p.canvas = null;
      p.el.classList.remove("ready");
    }
  }

  function watchPages() {
    const list = state.pages;
    const byEl = el => list[Number(el.dataset.n) - 1];
    if (!("IntersectionObserver" in window)) {
      list.forEach(p => { p.wanted = true; schedule(p); });
      return;
    }
    const near = new IntersectionObserver(entries => {
      for (const e of entries) if (e.isIntersecting) { const p = byEl(e.target); p.wanted = true; schedule(p); }
    }, { rootMargin: "130% 0px" });
    list.forEach(p => near.observe(p.el));
    if (isCoarse || isLowMemory) {
      const far = new IntersectionObserver(entries => {
        for (const e of entries) if (!e.isIntersecting) freePage(byEl(e.target));
      }, { rootMargin: "320% 0px" });
      list.forEach(p => far.observe(p.el));
    } else {
      // Large screens keep every page, so printing from the browser has all of them.
      const idle = window.requestIdleCallback || (fn => setTimeout(fn, 400));
      list.forEach(p => idle(() => { p.wanted = true; schedule(p); }));
    }
  }

  function refreshVisible() {
    for (const p of state.pages) if (p.wanted && needsRender(p)) schedule(p);
  }

  /* ---------- position: which page is under the middle of the screen ---------- */
  function pageAtMiddle() {
    const list = state.pages;
    if (!list.length) return 0;
    const top = list[0].el.getBoundingClientRect().top;
    const h = list[0].el.getBoundingClientRect().height;
    const mid = window.innerHeight / 2;
    if (mid < top || !h) return 0;
    return Math.min(list.length, Math.floor((mid - top) / h) + 1);
  }

  function showPosition() {
    const n = pageAtMiddle();
    state.current = n;
    const total = state.pages.length;
    const label = $("page-label");
    label.textContent = n ? "עמוד " + n + " מתוך " + total : "עמודי החוברת";
    const max = document.documentElement.scrollHeight - window.innerHeight;
    $("page-btn").style.setProperty("--done", (max > 0 ? Math.min(1, window.scrollY / max) * 100 : 0) + "%");
  }

  function savePosition() {
    const n = state.current;
    if (n) store.set(LAST_KEY, String(n));
    try { history.replaceState(null, "", n ? "#page-" + n : location.pathname + location.search); } catch (e) { /* file: */ }
  }

  function goToPage(n, smooth) {
    const p = state.pages[n - 1];
    if (!p) return;
    const top = p.el.getBoundingClientRect().top + window.scrollY - $("topbar").offsetHeight;
    const close = Math.abs(n - (state.current || 1)) <= 2;
    window.scrollTo({ top, behavior: smooth && close && !reducedMotion() ? "smooth" : "auto" });
  }

  function wireScrolling() {
    let queued = false, stopTimer;
    const onFrame = () => {
      queued = false;
      showPosition();
    };
    window.addEventListener("scroll", () => {
      if (!queued) { queued = true; requestAnimationFrame(onFrame); }
      clearTimeout(stopTimer);
      stopTimer = setTimeout(savePosition, 250);
    }, { passive: true });
  }

  /* ---------- zoom: double tap toggles it, pinch stays native and only sharpens the page ---------- */
  function baseWidth() { return Math.min($("pages-wrap").clientWidth, 794); }

  function applyWidth() {
    $("pages").style.width = state.zoom > 1 ? baseWidth() * state.zoom + "px" : "";
  }

  function setZoom(next, x, y) {
    const pages = $("pages"), wrap = $("pages-wrap");
    const before = pages.getBoundingClientRect();
    const fx = before.width ? (x - before.left) / before.width : 0.5;
    const fy = before.height ? (y - before.top) / before.height : 0;
    state.zoom = next;
    applyWidth();
    const after = pages.getBoundingClientRect();
    wrap.scrollLeft = Math.max(0, fx * after.width - (x - wrap.getBoundingClientRect().left));
    window.scrollTo({ top: after.top + window.scrollY + fy * after.height - y, behavior: "auto" });
    $("zoom-btn").hidden = next === 1;
    refreshVisible();
  }

  function wireZoom() {
    let last = 0, lx = 0, ly = 0, moved = false;
    const wrap = $("pages-wrap");
    const toggle = (x, y) => setZoom(state.zoom > 1 ? 1 : MAX_ZOOM, x, y);
    wrap.addEventListener("pointerdown", () => { moved = false; });
    wrap.addEventListener("pointermove", e => { if (e.pointerType === "touch" && (Math.abs(e.movementX) + Math.abs(e.movementY)) > 8) moved = true; });
    wrap.addEventListener("pointerup", e => {
      if (e.pointerType !== "touch" || moved || !e.isPrimary) return;
      const now = Date.now();
      if (now - last < 320 && Math.abs(e.clientX - lx) < 28 && Math.abs(e.clientY - ly) < 28) {
        last = 0;
        toggle(e.clientX, e.clientY);
      } else {
        last = now; lx = e.clientX; ly = e.clientY;
      }
    });
    wrap.addEventListener("dblclick", e => toggle(e.clientX, e.clientY));
    $("zoom-btn").addEventListener("click", () => setZoom(1, window.innerWidth / 2, window.innerHeight / 2));

    let t;
    const later = () => { clearTimeout(t); t = setTimeout(refreshVisible, 260); };
    if (window.visualViewport) window.visualViewport.addEventListener("resize", later);
    window.addEventListener("resize", () => {
      const n = state.current;
      applyWidth();
      if (n > 1) goToPage(n, false);
      later();
    });
  }

  /* ---------- download: a real file everywhere, and the share sheet where iPhones need it ---------- */
  function saveBlob(blob) {
    const url = URL.createObjectURL(blob);
    const a = Object.assign(document.createElement("a"), { href: url, download: FILE_NAME });
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
    toast("ההורדה התחילה");
  }

  function wireDownload() {
    $("pdf-btn").addEventListener("click", async e => {
      if (!state.blob) return; // the plain link still downloads while the file is loading
      e.preventDefault();
      if (isIOS && navigator.canShare && window.File) {
        const file = new File([state.blob], FILE_NAME, { type: "application/pdf" });
        if (navigator.canShare({ files: [file] })) {
          try { await navigator.share({ files: [file], title: TITLE }); }
          catch (err) { if (err.name !== "AbortError") window.location.href = PDF_URL; }
          return;
        }
      }
      if (isIOS && isStandalone()) { window.location.href = PDF_URL; return; }
      saveBlob(state.blob);
    });
  }

  /* ---------- pages sheet, built from the bookmarks inside the PDF ---------- */
  let lastFocus = null;
  function openSheet() {
    lastFocus = document.activeElement;
    $("sheet").hidden = false;
    $("sheet-close").focus();
    document.documentElement.classList.add("sheet-open");
  }
  function closeSheet() {
    $("sheet").hidden = true;
    document.documentElement.classList.remove("sheet-open");
    if (lastFocus) lastFocus.focus();
  }

  async function readBookmarks(pdf) {
    const outline = (await pdf.getOutline()) || [];
    const out = [];
    for (const item of outline) {
      const dest = typeof item.dest === "string" ? await pdf.getDestination(item.dest) : item.dest;
      if (dest && dest[0]) out.push({ title: item.title, n: (await pdf.getPageIndex(dest[0])) + 1 });
    }
    return out;
  }

  function buildSheet(marks) {
    const go = n => { closeSheet(); goToPage(n, true); };
    const button = (cls, text, n) => {
      const b = Object.assign(document.createElement("button"), { type: "button", className: cls, textContent: text });
      b.setAttribute("aria-label", typeof text === "number" || /^\d+$/.test(text) ? "שאלה " + text : text);
      b.addEventListener("click", () => go(n));
      return b;
    };
    const discs = $("sheet-questions"), links = $("sheet-sections");
    for (const m of marks) {
      const q = /^שאלה (\d+)$/.exec(m.title);
      if (q) discs.append(button("disc", q[1], m.n));
      else links.append(button("section", m.title, m.n));
    }
    if (!discs.children.length) {
      state.pages.forEach(p => discs.append(button("disc", String(p.n), p.n)));
      $("sheet-questions-title").textContent = "עמודים";
    }
  }

  function wireActions() {
    $("page-btn").addEventListener("click", openSheet);
    $("sheet-close").addEventListener("click", closeSheet);
    $("sheet").addEventListener("click", e => { if (e.target === $("sheet")) closeSheet(); });
    document.addEventListener("keydown", e => {
      if ($("sheet").hidden) return;
      if (e.key === "Escape") closeSheet();
      if (e.key === "Tab") {
        const items = [...$("sheet").querySelectorAll("button:not([hidden])")];
        const first = items[0], last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });

    $("share-btn").addEventListener("click", async () => {
      const url = location.origin + location.pathname;
      if (navigator.share) {
        try { await navigator.share({ title: TITLE, url }); } catch (e) { /* closed */ }
        return;
      }
      try { await navigator.clipboard.writeText(url); toast("הקישור הועתק"); }
      catch (e) { toast(url, null, 6000); }
    });

    // Install: the browser's own prompt on Android and computers, short directions on iPhone.
    const install = $("install-btn");
    const runInstall = async () => {
      if (state.installEvent) {
        const ev = state.installEvent;
        state.installEvent = null;
        install.hidden = true;
        ev.prompt();
        await ev.userChoice;
      } else if (isIOS) {
        $("ios-help").hidden = !$("ios-help").hidden;
      }
    };
    install.addEventListener("click", runInstall);
    window.addEventListener("beforeinstallprompt", e => {
      e.preventDefault();
      state.installEvent = e;
      if (!isStandalone()) install.hidden = false;
    });
    window.addEventListener("appinstalled", () => {
      install.hidden = true;
      store.set(INSTALL_KEY, "1");
      toast("האפליקציה הותקנה");
    });
    if (isIOS && !isStandalone()) install.hidden = false;

    setTimeout(() => {
      if (isStandalone() || store.get(INSTALL_KEY) || !isCoarse || !(state.installEvent || isIOS)) return;
      store.set(INSTALL_KEY, "1");
      toast("אפשר להתקין את החוברת כאפליקציה בטלפון", {
        label: "התקנה",
        run: () => { if (isIOS) { openSheet(); $("ios-help").hidden = false; } else runInstall(); },
      }, 9000);
    }, 12000);
  }

  /* ---------- start ---------- */
  function requestedPage() {
    const m = /^#page-(\d+)$/.exec(location.hash);
    return m ? Number(m[1]) : 0;
  }

  async function start() {
    const host = $("pages");
    try {
      const bytes = await loadBytes();
      state.blob = new Blob([bytes], { type: "application/pdf" });
      pdfjsLib.GlobalWorkerOptions.workerSrc = "vendor/pdfjs-3.11.174/pdf.worker.min.js";
      const pdf = await pdfjsLib.getDocument({ data: bytes, isEvalSupported: false }).promise;

      const pages = await Promise.all(Array.from({ length: pdf.numPages }, (_, i) => pdf.getPage(i + 1)));
      const frag = document.createDocumentFragment();
      pages.forEach((page, i) => {
        const base = page.getViewport({ scale: 1 });
        const el = document.createElement("div");
        el.className = "pdf-page";
        el.dataset.n = String(i + 1);
        el.setAttribute("role", "img");
        el.setAttribute("aria-label", "עמוד " + (i + 1) + " מתוך " + pdf.numPages);
        el.style.setProperty("--ratio", base.width + " / " + base.height);
        const mark = document.createElement("span");
        mark.className = "ph";
        mark.setAttribute("aria-hidden", "true");
        mark.textContent = String(i + 1);
        el.append(mark);
        frag.append(el);
        state.pages.push({ n: i + 1, el, page, base, canvas: null, renderedWidth: 0, task: null, wanted: false });
      });
      host.append(frag);
      $("loading").hidden = true;

      const wanted = requestedPage();
      if (wanted) goToPage(wanted, false);
      showPosition();
      watchPages();
      buildSheet(await readBookmarks(pdf));

      const last = Number(store.get(LAST_KEY));
      if (!wanted && last > 1 && last <= pdf.numPages) {
        toast("להמשיך מעמוד " + last + "?", { label: "המשך", run: () => goToPage(last, false) }, 7000);
      }
    } catch (err) {
      console.error(err);
      const el = $("loading");
      el.hidden = false;
      el.textContent = "לא ניתן להציג את העמודים כעת. אפשר לפתוח את הקובץ ישירות: ";
      el.append(Object.assign(document.createElement("a"), { href: PDF_URL, textContent: "פתיחת ה-PDF" }));
    }
  }

  wireScrolling();
  wireZoom();
  wireDownload();
  wireActions();
  start();

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("sw.js").catch(err => console.warn("offline mode unavailable", err));
    });
  }
})();
