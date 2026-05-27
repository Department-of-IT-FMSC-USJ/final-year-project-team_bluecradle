import { db, preSyncInfants } from "./db.js";

// ── Register Service Worker ──────────────────────────────────────
async function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) {
    console.warn("Service Worker not supported in this browser.");
    return;
  }

  try {
    const registration = await navigator.serviceWorker.register(
      "/static/sw/service-worker.js",
      { type: "module" },
    );
    console.log("Service Worker registered:", registration.scope);

    // Register background sync tag.
    if ("sync" in registration) {
      await registration.sync.register("bluecradle-sync");
    }
  } catch (err) {
    console.error("Service Worker registration failed:", err);
  }
}

// ── Monitor network — queue sync when back online ────────────────
function registerConnectivityListeners() {
  window.addEventListener("online", async () => {
    console.log("Network restored — triggering sync.");
    const registration = await navigator.serviceWorker.ready;
    if ("sync" in registration) {
      await registration.sync.register("bluecradle-sync");
    }
  });

  window.addEventListener("offline", () => {
    console.log("Network lost — entering offline mode.");
  });
}

// ── Pre-sync infants on app load ─────────────────────────────────
async function initialPreSync() {
  try {
    await preSyncInfants(db);
    console.log("Infant profiles pre-synced to IndexedDB.");
  } catch (err) {
    console.warn("Pre-sync failed — continuing offline.", err);
  }
}

// ── Bootstrap ────────────────────────────────────────────────────
(async () => {
  await registerServiceWorker();
  registerConnectivityListeners();
  await initialPreSync();
})();
