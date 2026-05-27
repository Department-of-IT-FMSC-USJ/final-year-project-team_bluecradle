import { getUnsyncedEvents, markEventSynced } from "./db.js";

const API_BASE = "/api/clinic";

// ── Get JWT token from localStorage ─────────────────────────────
function getToken() {
  return localStorage.getItem("access_token");
}

// ── Post a single event to Django ───────────────────────────────
async function postEvent(event) {
  const response = await fetch(`${API_BASE}/events/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getToken()}`,
    },
    body: JSON.stringify(event.payload_json),
  });
  return response.ok;
}

// ── Main sync function — called by Service Worker ────────────────
export async function syncQueue() {
  const events = await getUnsyncedEvents();

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
      // Network dropped mid-sync — stop and retry next time.
      console.error("Sync failed for event:", event.local_id, err);
      break;
    }
  }

  return { synced: syncedCount };
}

// ── Pre-sync: pull all infants for logged-in PHM into IndexedDB ──
export async function preSyncInfants(db) {
  const response = await fetch("/api/infants/", {
    headers: { Authorization: `Bearer ${getToken()}` },
  });

  if (!response.ok) return;

  const infants = await response.json();
  const tx = db.transaction("infants", "readwrite");
  for (const infant of infants) {
    await tx.store.put(infant);
  }
  await tx.done;
}
