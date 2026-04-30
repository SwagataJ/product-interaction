/**
 * SSE event stream consumer for demo mode.
 * Connects to /api/events/stream and dispatches events to Zustand.
 */

import { useStore } from "./store";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let eventSource: EventSource | null = null;

export function startEventStream(speed: number = 100) {
  stopEventStream();

  const url = `${API_BASE}/api/events/stream?speed=${speed}`;
  eventSource = new EventSource(url);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      const store = useStore.getState();

      // Update sim time
      if (data.timestamp) {
        store.setCurrentSimTime(data.timestamp);
      }

      // Add to live events
      store.addLiveEvent({
        event_id: data.event_id || crypto.randomUUID(),
        tag_id: data.tag_id || "",
        sku_id: data.sku_id || "",
        zone_from: data.zone_from || null,
        zone_to: data.zone_to || "",
        event_type: data.event_type || "",
        timestamp: data.timestamp || "",
      });
    } catch {
      // Ignore parse errors
    }
  };

  eventSource.onerror = () => {
    // Auto-reconnect is handled by EventSource
  };
}

export function stopEventStream() {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
  useStore.getState().clearLiveEvents();
}
