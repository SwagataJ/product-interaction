import { create } from "zustand";

export type TabId = "live_store" | "analytics" | "executive";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolBadges?: string[];
  inlineChart?: Record<string, unknown>;
}

export interface DashboardEvent {
  event_id: string;
  tag_id: string;
  sku_id: string;
  zone_from: string | null;
  zone_to: string;
  event_type: string;
  timestamp: string;
}

interface DashboardState {
  // Tab navigation
  activeTab: TabId;
  setActiveTab: (tab: TabId) => void;
  pendingAutoSwitch: TabId | null;

  // Filters
  selectedTimeRange: { from: string; to: string } | null;
  gridFilter: { category?: string; sku?: string; fixture?: string };
  setGridFilter: (filter: { category?: string; sku?: string; fixture?: string }) => void;
  clearGridFilter: () => void;

  // Chat
  chatOpen: boolean;
  setChatOpen: (open: boolean) => void;
  chatMessages: Message[];
  addMessage: (msg: Message) => void;
  chatPendingContext: string | null;
  setChatPendingContext: (ctx: string | null) => void;

  // Dashboard reactions to AI
  highlightedFixtures: string[];
  setHighlightedFixtures: (ids: string[]) => void;
  tracingSkuJourney: string | null;

  // Demo mode
  demoMode: boolean;
  setDemoMode: (on: boolean) => void;
  demoSpeed: number;
  setDemoSpeed: (speed: number) => void;
  currentSimTime: string | null;
  setCurrentSimTime: (time: string) => void;
  isAfterHours: boolean;
  liveEvents: DashboardEvent[];
  addLiveEvent: (evt: DashboardEvent) => void;
  clearLiveEvents: () => void;
}

export const useStore = create<DashboardState>((set) => ({
  activeTab: "analytics",
  setActiveTab: (tab) => set({ activeTab: tab }),
  pendingAutoSwitch: null,

  selectedTimeRange: null,
  gridFilter: {},
  setGridFilter: (filter) => set({ gridFilter: filter }),
  clearGridFilter: () => set({ gridFilter: {} }),

  chatOpen: false,
  setChatOpen: (open) => set({ chatOpen: open }),
  chatMessages: [],
  addMessage: (msg) =>
    set((state) => ({ chatMessages: [...state.chatMessages, msg] })),
  chatPendingContext: null,
  setChatPendingContext: (ctx) => set({ chatPendingContext: ctx }),

  highlightedFixtures: [],
  setHighlightedFixtures: (ids) => set({ highlightedFixtures: ids }),
  tracingSkuJourney: null,

  demoMode: false,
  setDemoMode: (on) => set({ demoMode: on }),
  demoSpeed: 100,
  setDemoSpeed: (speed) => set({ demoSpeed: speed }),
  currentSimTime: null,
  setCurrentSimTime: (time) => {
    // Handle both "2026-04-18 10:00:00" and ISO "2026-04-18T10:00:00" formats
    const timePart = time.split(/[T ]/)[1] || "12:00";
    const hour = parseInt(timePart.split(":")[0]);
    set({ currentSimTime: time, isAfterHours: hour >= 22 || hour < 10 });
  },
  isAfterHours: false,
  liveEvents: [],
  addLiveEvent: (evt) =>
    set((state) => ({
      liveEvents: [...state.liveEvents.slice(-99), evt],
    })),
  clearLiveEvents: () => set({ liveEvents: [] }),
}));
