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

// ── Web Push Subscription ─────────────────────────────────────────────────────
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64  = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const output  = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; i++) {
        output[i] = rawData.charCodeAt(i);
    }
    return output;
}

function getNotifCookie(name) {
    const parts = ('; ' + document.cookie).split('; ' + name + '=');
    return parts.length === 2 ? parts.pop().split(';').shift() : '';
}

async function sendSubscriptionToServer(subscription) {
    const sub = subscription.toJSON();
    await fetch('/api/notifications/subscribe/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getNotifCookie('csrftoken'),
        },
        body: JSON.stringify({ endpoint: sub.endpoint, keys: sub.keys }),
    });
}

async function subscribeToPush() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;

    const permission = await Notification.requestPermission();
    if (permission !== 'granted') return;

    try {
        const reg      = await navigator.serviceWorker.ready;
        const existing = await reg.pushManager.getSubscription();

        if (existing) {
            await sendSubscriptionToServer(existing);
            return;
        }

        const vapidKey     = window.VAPID_PUBLIC_KEY;
        const subscription = await reg.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(vapidKey),
        });

        await sendSubscriptionToServer(subscription);
    } catch (e) {
        console.error('Push subscription failed:', e);
    }
}

subscribeToPush();
