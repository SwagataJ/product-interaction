"use client";

import { useStore, type TabId } from "@/lib/store";
import { Play, Pause, Clock } from "lucide-react";

const TABS: { id: TabId; label: string }[] = [
  { id: "live_store", label: "Live Store" },
  { id: "analytics", label: "Analytics" },
  { id: "executive", label: "Executive Summary" },
];

const SPEEDS = [50, 100, 200, 500];

export default function TopBar() {
  const { activeTab, setActiveTab, demoMode, setDemoMode, demoSpeed, setDemoSpeed, currentSimTime } = useStore();

  return (
    <header className="glass-card flex items-center justify-between px-4 py-2 mx-4 mt-3 mb-2">
      {/* Store name */}
      <div className="flex items-center gap-3">
        <div className="w-2 h-2 rounded-full bg-[var(--accent-mint)] animate-pulse" />
        <span className="text-sm font-medium text-[var(--text-primary)]">
          Westside, Palladium Mumbai
        </span>
      </div>

      {/* Tab navigation */}
      <nav className="flex items-center gap-1 bg-[var(--bg-deep)] rounded-lg p-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
              activeTab === tab.id
                ? "bg-[var(--accent-cyan)] text-[var(--bg-deep)]"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Demo controls + time */}
      <div className="flex items-center gap-3">
        {currentSimTime && (
          <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
            <Clock size={12} />
            <span className="font-tabular">
              {new Date(currentSimTime).toLocaleTimeString("en-IN", {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
          </div>
        )}

        <select
          value={demoSpeed}
          onChange={(e) => setDemoSpeed(Number(e.target.value))}
          className="bg-[var(--bg-deep)] text-[var(--text-muted)] text-xs px-2 py-1 rounded border border-[var(--border)]"
        >
          {SPEEDS.map((s) => (
            <option key={s} value={s}>
              {s}x
            </option>
          ))}
        </select>

        <button
          onClick={() => {
            if (!demoMode) setActiveTab("live_store");
            setDemoMode(!demoMode);
          }}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
            demoMode
              ? "bg-[var(--accent-coral)] text-white"
              : "bg-[var(--accent-cyan)] text-[var(--bg-deep)]"
          }`}
        >
          {demoMode ? <Pause size={12} /> : <Play size={12} />}
          {demoMode ? "Stop" : "Demo"}
        </button>
      </div>
    </header>
  );
}
