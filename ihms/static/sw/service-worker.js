import { syncQueue } from "../js/sync.js";

const CACHE_NAME = "bluecradle-v1";

// Files to cache for offline app shell
const APP_SHELL = [
  "/",
  "/static/js/db.js",
  "/static/js/sync.js",
  "/static/css/main.css",
];

// ── Install — cache app shell ────────────────────────────────────
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)),
  );
  self.skipWaiting();
});

// ── Activate — clean up old caches ──────────────────────────────
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== CACHE_NAME)
            .map((key) => caches.delete(key)),
        ),
      ),
  );
  self.clients.claim();
});

// ── Fetch — serve from cache, fall back to network ───────────────
self.addEventListener("fetch", (event) => {
  // API calls always go to network — never serve from cache.
  if (event.request.url.includes("/api/")) {
    event.respondWith(fetch(event.request));
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request);
    }),
  );
});

// ── Background Sync — fires when connectivity is restored ────────
self.addEventListener("sync", (event) => {
  if (event.tag === "bluecradle-sync") {
    event.waitUntil(syncQueue());
  }
});

// ── Push Notifications — receives push from Django/Celery ────────
self.addEventListener("push", (event) => {
  const data = event.data?.json() ?? {};
  event.waitUntil(
    self.registration.showNotification(data.title || "BlueCradle", {
      body: data.body || "",
      icon: "/static/img/icon-192.png",
    }),
  );
});
