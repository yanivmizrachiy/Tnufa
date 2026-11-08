"use strict";
/* Offline support for the phone app.
   The page is fetched from the network first, so a new exam reaches teachers at once.
   Versioned files never change, so they come from the cache. */
const VERSION = "23";
const CACHE = "tnufa-" + VERSION;
const FONTS = "tnufa-fonts";
const SHELL = [
  "./",
  "checklist.html",
  "manifest.webmanifest",
  "viewer.css?v=21",
  "viewer.js?v=20",
  "exam.pdf?v=12",
  "vendor/pdfjs-3.11.174/pdf.min.js",
  "vendor/pdfjs-3.11.174/pdf.worker.min.js",
  "assets/logo.svg",
  "assets/cover.jpg",
  "assets/icons/icon-192.png",
  "assets/icons/icon-512.png",
];

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE && k !== FONTS).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

async function networkFirstPage(request) {
  const cache = await caches.open(CACHE);
  try {
    const res = await fetch(request);
    if (res.ok) await cache.put(request, res.clone());
    return res;
  } catch (err) {
    const hit = await cache.match(request);
    if (hit) return hit;
    throw err;
  }
}

async function cacheFirst(request) {
  const cache = await caches.open(CACHE);
  const hit = await cache.match(request);
  if (hit) return hit;
  const res = await fetch(request);
  if (res.ok) await cache.put(request, res.clone());
  return res;
}

async function fonts(request) {
  const cache = await caches.open(FONTS);
  const hit = await cache.match(request);
  const fresh = fetch(request).then(res => {
    if (res.ok || res.type === "opaque") cache.put(request, res.clone());
    return res;
  });
  if (hit) {
    fresh.catch(() => {});
    return hit;
  }
  return fresh;
}

self.addEventListener("fetch", event => {
  const { request } = event;
  if (request.method !== "GET" || request.headers.has("range")) return;
  const url = new URL(request.url);
  if (request.mode === "navigate") {
    event.respondWith(networkFirstPage(request));
  } else if (url.origin === self.location.origin) {
    event.respondWith(cacheFirst(request));
  } else if (url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com") {
    event.respondWith(fonts(request));
  }
});
