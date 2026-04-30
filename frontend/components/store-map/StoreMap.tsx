"use client";

import { useEffect, useState } from "react";
import { useStore } from "@/lib/store";
import { getStoreLayout, getFixtureHeatmap, type StoreLayout, type FixtureHeat } from "@/lib/api";
import Fixture from "./Fixture";
import FlowDots from "./FlowDots";

const SVG_W = 870;
const SVG_H = 490;

const ZONE_STYLE: Record<string, { fill: string; stroke: string; label: string }> = {
  backroom:   { fill: "#1a2240", stroke: "#2a3660", label: "#6B7A99" },
  trial_room: { fill: "#0f2a3a", stroke: "#00D4FF30", label: "#00D4FF" },
  till:       { fill: "#0f2a1e", stroke: "#00E5A040", label: "#00E5A0" },
  exit:       { fill: "#2a1a1e", stroke: "#FF4D6D40", label: "#FF4D6D" },
};

export default function StoreMap() {
  const [layout, setLayout] = useState<StoreLayout | null>(null);
  const [heatmap, setHeatmap] = useState<Record<string, number>>({});
  const [maxHeat, setMaxHeat] = useState(1);
  const { highlightedFixtures, isAfterHours, demoMode, liveEvents } = useStore();

  useEffect(() => {
    getStoreLayout().then(setLayout);
    getFixtureHeatmap().then((data) => {
      const map: Record<string, number> = {};
      let max = 1;
      data.forEach((f: FixtureHeat) => {
        map[f.fixture_id] = f.pickups_per_tag;
        if (f.pickups_per_tag > max) max = f.pickups_per_tag;
      });
      setHeatmap(map);
      setMaxHeat(max);
    });
  }, []);

  if (!layout) {
    return (
      <div className="glass-card flex items-center justify-center h-full flex-1">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-[var(--accent-cyan)] border-t-transparent rounded-full animate-spin" />
          <p className="text-[var(--text-muted)] text-xs">Loading store map...</p>
        </div>
      </div>
    );
  }

  // Build zone center lookup for flow dots
  const zoneCenters: Record<string, { x: number; y: number }> = {};
  layout.zones.forEach((z) => {
    zoneCenters[z.id] = { x: z.x + z.w / 2, y: z.y + z.h / 2 };
  });

  const fixtures = layout.zones.filter((z) => z.type === "fixture");
  const others = layout.zones.filter((z) => z.type !== "fixture" && z.type !== "exit");

  return (
    <div className={`glass-card relative overflow-hidden transition-all duration-700 h-full flex flex-col ${isAfterHours ? "after-hours-dim" : ""}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-3 pb-1">
        <div className="flex items-center gap-2">
          <div className={`w-1.5 h-1.5 rounded-full ${demoMode ? "bg-[var(--accent-mint)] animate-pulse" : "bg-[var(--text-dim)]"}`} />
          <span className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">
            Store Floor Plan
          </span>
        </div>
        {isAfterHours && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[var(--ops-amber)]/20 border border-[var(--ops-amber)]/30">
            <div className="w-1.5 h-1.5 rounded-full bg-[var(--ops-amber)] animate-pulse" />
            <span className="text-[10px] font-medium text-[var(--ops-amber)]">After-hours</span>
          </div>
        )}
        {demoMode && !isAfterHours && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[var(--accent-mint)]/10 border border-[var(--accent-mint)]/20">
            <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent-mint)] animate-pulse" />
            <span className="text-[10px] font-medium text-[var(--accent-mint)]">Live</span>
          </div>
        )}
      </div>

      {/* Map SVG */}
      <div className="px-3 pb-3 flex-1 min-h-0 flex items-center justify-center">
        <svg viewBox={`0 0 ${SVG_W} ${SVG_H}`} className="w-full h-full" preserveAspectRatio="xMidYMid meet">
          <defs>
            {/* Grid pattern */}
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.02)" strokeWidth="0.5" />
            </pattern>
            {/* Glow filter for highlighted fixtures */}
            <filter id="glow">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            {/* Heat gradient */}
            <linearGradient id="heatLow" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#1B3358" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#1B3358" stopOpacity="0.5" />
            </linearGradient>
            <linearGradient id="heatHigh" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#FF7A45" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#FF2E63" stopOpacity="0.5" />
            </linearGradient>
          </defs>

          {/* Background */}
          <rect width={SVG_W} height={SVG_H} fill="#0D1220" rx={8} />
          <rect width={SVG_W} height={SVG_H} fill="url(#grid)" rx={8} />

          {/* Store boundary */}
          <rect x={20} y={10} width={SVG_W - 40} height={SVG_H - 20} rx={6} fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth={1} strokeDasharray="8 4" />

          {/* Non-fixture zones */}
          {others.map((zone) => {
            const style = ZONE_STYLE[zone.type] || ZONE_STYLE.backroom;
            return (
              <g key={zone.id}>
                <rect
                  x={zone.x}
                  y={zone.y}
                  width={zone.w}
                  height={zone.h}
                  rx={6}
                  fill={style.fill}
                  stroke={style.stroke}
                  strokeWidth={1}
                />
                {/* Icon/label area */}
                <text
                  x={zone.x + zone.w / 2}
                  y={zone.y + zone.h / 2 - 4}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fill={style.label}
                  fontSize={10}
                  fontWeight={600}
                  letterSpacing="0.05em"
                >
                  {zone.type === "backroom" ? "BACKROOM" :
                   zone.type === "trial_room" ? "TRIAL ROOMS" :
                   zone.type === "till" ? "TILL" :
                   zone.type === "exit" ? "EXIT" : zone.label}
                </text>
                <text
                  x={zone.x + zone.w / 2}
                  y={zone.y + zone.h / 2 + 10}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fill={style.label}
                  fontSize={7}
                  opacity={0.5}
                >
                  {zone.id}
                </text>
              </g>
            );
          })}

          {/* Fixture zones */}
          {fixtures.map((zone) => (
            <Fixture
              key={zone.id}
              zone={zone}
              heatValue={heatmap[zone.id] || 0}
              maxHeat={maxHeat}
              isHighlighted={highlightedFixtures.includes(zone.id)}
            />
          ))}

          {/* Flow dots layer */}
          {liveEvents.length > 0 && (
            <FlowDots events={liveEvents} zoneCenters={zoneCenters} isAfterHours={isAfterHours} />
          )}

          {/* Heat legend */}
          <g transform={`translate(${SVG_W - 130}, ${SVG_H - 35})`}>
            <text x={0} y={0} fill="#7A8497" fontSize={8} fontWeight={500}>ENGAGEMENT</text>
            <rect x={0} y={6} width={100} height={6} rx={3} fill="#1B3358" />
            <rect x={50} y={6} width={50} height={6} rx={3} fill="#FF7A45" opacity={0.8} />
            <text x={0} y={22} fill="#4A5160" fontSize={7}>Low</text>
            <text x={90} y={22} fill="#4A5160" fontSize={7}>High</text>
          </g>
        </svg>
      </div>
    </div>
  );
}
