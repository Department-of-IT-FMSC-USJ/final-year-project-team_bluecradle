import { getUnsyncedEvents, markEventSynced } from "./db.js";

const API_BASE = "/api/clinic";

// ── CSRF helper ──────────────────────────────────────────────────
function getCsrf() {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : "";
}

// ── Post a single event to Django ───────────────────────────────
async function postEvent(event) {
  const response = await fetch(`${API_BASE}/events/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrf(),
    },
    credentials: "include",
    body: JSON.stringify({
      infant: event.payload_json.infant_phn,
      session: event.payload_json.session_id,
      event_type: event.event_type,
      fhb_service_code: event.fhb_service_code,
      priority: event.priority,
      payload_json: event.payload_json,
      event_timestamp: event.event_timestamp,
    }),
  });
  return response.ok;
}

// ── Main sync function ───────────────────────────────────────────
export async function syncQueue() {
  const events = await getUnsyncedEvents();
  console.log("syncQueue events found:", events.length);
  for (const e of events) {
    console.log("event:", e.local_id, e.is_synced, e.event_type);
  }
  if (events.length === 0) return { synced: 0 };

  let syncedCount = 0;

  for (const event of events) {
    try {
      const success = await postEvent(event);
      if (success) {
        await markEventSynced(event.local_id);
        syncedCount++;
      }
    } catch (err) {
      console.error("Sync failed for event:", event.local_id, err);
      break;
    }
  }

  // ── Notify PHM after successful sync ────────────────────────
  if (syncedCount > 0) {
    try {
      await fetch("/api/notifications/sync-confirm/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrf(),
        },
        credentials: "include",
        body: JSON.stringify({ record_count: syncedCount }),
      });
    } catch (e) {
      console.warn("Sync confirm notification failed:", e);
    }
  }

  return { synced: syncedCount };
}

// ── Pre-sync: pull all infants for logged-in PHM into IndexedDB ──
export async function preSyncInfants(db) {
  const response = await fetch("/api/infants/list/", {
    headers: { "X-CSRFToken": getCsrf() },
    credentials: "include",
  });

  if (!response.ok) return;

  const infants = await response.json();
  const tx = db.transaction("infants", "readwrite");
  for (const infant of infants) {
    await tx.store.put(infant);
  }
  await tx.done;

  // ── Cache infant pages for offline use ──────────────────────
  const pagesToCache = [];
  for (const infant of infants) {
    pagesToCache.push(`/clinic/phm/infants/${infant.phn}/`);
    pagesToCache.push(`/clinic/phm/infants/${infant.phn}/growth/`);
    pagesToCache.push(`/clinic/phm/infants/${infant.phn}/immunization/`);
  }
  pagesToCache.push("/clinic/phm/");
  pagesToCache.push("/clinic/phm/infants/");

  if ("serviceWorker" in navigator) {
    const reg = await navigator.serviceWorker.ready;
    reg.active?.postMessage({ type: "CACHE_PAGES", pages: pagesToCache });
  }
}
