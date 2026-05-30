async function syncQueue() {
  const allClients = await self.clients.matchAll();
  for (const client of allClients) {
    client.postMessage({ type: "SYNC_REQUESTED" });
  }
}

const CACHE_NAME = "bluecradle-v1";
const PAGES_CACHE = "bluecradle-pages-v1";

const APP_SHELL = ["/static/js/db.js", "/static/js/sync.js"];

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
            .filter((key) => key !== CACHE_NAME && key !== PAGES_CACHE)
            .map((key) => caches.delete(key)),
        ),
      ),
  );
  self.clients.claim();
});

// ── Fetch — serve from cache, fall back to network ───────────────
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // API calls always go to network
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(fetch(event.request));
    return;
  }

  // Static files — cache first
  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        return (
          cached ||
          fetch(event.request).then((response) => {
            const clone = response.clone();
            caches
              .open(CACHE_NAME)
              .then((cache) => cache.put(event.request, clone));
            return response;
          })
        );
      }),
    );
    return;
  }

  // HTML pages — network first, fall back to cache
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const clone = response.clone();
        caches
          .open(PAGES_CACHE)
          .then((cache) => cache.put(event.request, clone));
        return response;
      })
      .catch(() => caches.match(event.request)),
  );
});

// ── Background Sync ──────────────────────────────────────────────
self.addEventListener("sync", (event) => {
  if (event.tag === "bluecradle-sync") {
    event.waitUntil(syncQueue());
  }
});

// ── Push Notifications ───────────────────────────────────────────
self.addEventListener("push", (event) => {
  const data = event.data?.json() ?? {};
  event.waitUntil(
    self.registration.showNotification(data.title || "BlueCradle", {
      body: data.body || "",
      icon: "/static/img/icon-192.png",
    }),
  );
});

// ── Message from page — trigger sync ────────────────────────────
self.addEventListener("message", (event) => {
  if (event.data?.type === "CACHE_PAGES") {
    const pages = event.data.pages;
    caches.open(PAGES_CACHE).then((cache) => {
      pages.forEach((url) => {
        fetch(url)
          .then((response) => {
            if (response.ok) cache.put(url, response);
          })
          .catch(() => {});
      });
    });
  }
});
