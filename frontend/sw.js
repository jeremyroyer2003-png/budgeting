/**
 * ClearBudget Service Worker
 * Strategy: cache-first for static assets, network-first for API calls.
 */

const CACHE = "clearbudget-v1";

const STATIC = [
  "/",
  "/index.html",
  "/css/style.css",
  "/js/api.js",
  "/js/app.js",
  "/js/auth.js",
  "/js/dashboard.js",
  "/js/transactions.js",
  "/js/budgets.js",
  "/js/goals.js",
  "/js/subscriptions.js",
  "/js/alerts.js",
  "/js/insights.js",
  "/js/family.js",
  "/icons/icon-192.svg",
  "/icons/icon-512.svg",
];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(STATIC)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);

  // API calls (port 5000 or /api/ path) — network-first, no caching
  if (url.port === "5000" || url.pathname.startsWith("/api/")) {
    e.respondWith(fetch(e.request).catch(() => new Response(
      JSON.stringify({ error: "You appear to be offline" }),
      { headers: { "Content-Type": "application/json" }, status: 503 }
    )));
    return;
  }

  // External CDN (Chart.js, Feather, Plaid) — network-first with cache fallback
  if (url.hostname !== self.location.hostname) {
    e.respondWith(
      caches.match(e.request).then(cached =>
        fetch(e.request).then(res => {
          caches.open(CACHE).then(c => c.put(e.request, res.clone()));
          return res;
        }).catch(() => cached || new Response("", { status: 503 }))
      )
    );
    return;
  }

  // Static assets — cache-first
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request).then(res => {
      if (res.ok) {
        caches.open(CACHE).then(c => c.put(e.request, res.clone()));
      }
      return res;
    }))
  );
});
