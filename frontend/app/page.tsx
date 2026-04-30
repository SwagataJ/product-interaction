"use client";

import { useEffect } from "react";
import { useStore } from "@/lib/store";
import TopBar from "@/components/topbar/TopBar";
import KpiStrip from "@/components/kpi/KpiStrip";
import BusinessKpiStrip from "@/components/kpi/BusinessKpiStrip";
import ChartGrid from "@/components/grid/ChartGrid";
import StoreMap from "@/components/store-map/StoreMap";
import ChatPanel from "@/components/chat/ChatPanel";
import ExecutiveSummary from "@/components/exec/ExecutiveSummary";
import { startEventStream, stopEventStream } from "@/lib/eventStream";

export default function Home() {
  const activeTab = useStore((s) => s.activeTab);
  const demoMode = useStore((s) => s.demoMode);
  const demoSpeed = useStore((s) => s.demoSpeed);

  // Wire demo mode to SSE event stream
  useEffect(() => {
    if (demoMode) {
      startEventStream(demoSpeed);
    } else {
      stopEventStream();
    }
    return () => stopEventStream();
  }, [demoMode, demoSpeed]);

  return (
    <div className="flex flex-col h-full min-h-screen bg-[var(--bg-deep)]">
      <TopBar />
      <main className={`flex-1 min-h-0 ${activeTab === "live_store" ? "flex flex-col px-0 pt-0 pb-0 overflow-hidden" : "overflow-y-auto px-3 pt-2 pb-4"}`}>
        {activeTab === "live_store" && (
          <>
            <div className="px-3 pt-2 pb-1 flex-shrink-0">
              <KpiStrip />
            </div>
            <div className="flex-1 min-h-0 px-2 pb-2">
              <StoreMap />
            </div>
          </>
        )}

        {activeTab === "analytics" && (
          <div className="flex flex-col gap-3">
            <KpiStrip />
            <BusinessKpiStrip />
            <ChartGrid />
          </div>
        )}

        {activeTab === "executive" && <ExecutiveSummary />}
      </main>

      {/* Chat panel persists across all tabs */}
      <ChatPanel />
    </div>
  );
}
