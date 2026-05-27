import { openDB } from "https://cdn.jsdelivr.net/npm/idb@7/+esm";

const DB_NAME = "bluecradle";
const DB_VERSION = 1;

export const db = await openDB(DB_NAME, DB_VERSION, {
  upgrade(db) {
    // Infants store — pre-synced from Django at session start
    if (!db.objectStoreNames.contains("infants")) {
      const infantStore = db.createObjectStore("infants", { keyPath: "phn" });
      infantStore.createIndex("registered_phm", "registered_phm");
    }

    // Growth records store
    if (!db.objectStoreNames.contains("growth_records")) {
      const grStore = db.createObjectStore("growth_records", {
        keyPath: "local_id",
        autoIncrement: true,
      });
      grStore.createIndex("infant_phn", "infant_phn");
      grStore.createIndex("is_synced", "is_synced");
    }

    // Immunization events store
    if (!db.objectStoreNames.contains("immunization_events")) {
      const imStore = db.createObjectStore("immunization_events", {
        keyPath: "local_id",
        autoIncrement: true,
      });
      imStore.createIndex("infant_phn", "infant_phn");
      imStore.createIndex("is_synced", "is_synced");
    }

    // FHB atomic events store — the sync queue
    if (!db.objectStoreNames.contains("atomic_events")) {
      const aeStore = db.createObjectStore("atomic_events", {
        keyPath: "local_id",
        autoIncrement: true,
      });
      aeStore.createIndex("is_synced", "is_synced");
      aeStore.createIndex("priority", "priority");
    }

    // Clinic sessions store
    if (!db.objectStoreNames.contains("clinic_sessions")) {
      db.createObjectStore("clinic_sessions", {
        keyPath: "local_id",
        autoIncrement: true,
      });
    }
  },
});

// ── Helper: get all unsynced events sorted by priority ──────────
export async function getUnsyncedEvents() {
  const all = await db.getAllFromIndex("atomic_events", "is_synced", 0);
  const priorityOrder = { CRITICAL_HIGH: 0, CRITICAL: 1, STANDARD: 2 };
  return all.sort(
    (a, b) => priorityOrder[a.priority] - priorityOrder[b.priority],
  );
}

// ── Helper: mark event as synced ────────────────────────────────
export async function markEventSynced(local_id) {
  const tx = db.transaction("atomic_events", "readwrite");
  const event = await tx.store.get(local_id);
  if (event) {
    event.is_synced = 1;
    await tx.store.put(event);
  }
  await tx.done;
}
