"use client";

import { useEffect, useState, useRef } from "react";
import type { DashboardEvent } from "@/lib/store";

interface FlowDotsProps {
  events: DashboardEvent[];
  zoneCenters: Record<string, { x: number; y: number }>;
  isAfterHours: boolean;
}

interface ActiveJourney {
  id: string;
  tagId: string;
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
  progress: number;
  eventType: string;
  startTime: number;
  zoneTo: string;
  zoneFrom: string;
}

// How long each dot travels (ms)
const TRAVEL_DURATION = 3000;
// How long a dot pulses at destination after arriving
const LINGER_DURATION = 2000;
const MAX_ACTIVE = 60;

// Events to skip entirely (not interesting visually)
const SKIP_EVENTS = new Set(["BASKET_DWELL", "RECEIVED_BACKROOM", "EXITED_STORE"]);

// Events to throttle (show only ~1 in N)
const THROTTLE_EVENTS: Record<string, number> = {
  MOVED_TO_FLOOR: 15,      // show 1 in 15
  RETURNED_TO_FIXTURE: 3,  // show 1 in 3
};

// For same-zone events, override destination to make travel visible
const ZONE_OVERRIDES: Record<string, string> = {
  EXITED_TRIAL_PURCHASED: "TILL_RANDOM",
  EXITED_TRIAL_REJECTED:  "", // will pick a random fixture
  EXITED_STORE:           "EXIT",
};

const EVENT_CONFIG: Record<string, { color: string; label: string; size: number }> = {
  MOVED_TO_FLOOR:          { color: "#FFB800", label: "→ Floor",       size: 4 },
  PICKED_UP:               { color: "#00D4FF", label: "Picked up",     size: 6 },
  ENTERED_TRIAL:           { color: "#9D7EFF", label: "→ Trial Room",  size: 6 },
  EXITED_TRIAL_PURCHASED:  { color: "#00E5A0", label: "Purchased! →",  size: 7 },
  EXITED_TRIAL_REJECTED:   { color: "#FF4D6D", label: "Rejected",      size: 5 },
  SOLD_AT_TILL:            { color: "#00E5A0", label: "Sold at Till",   size: 7 },
  MISPLACED:               { color: "#FF4D6D", label: "Misplaced",     size: 4 },
  EXITED_STORE:            { color: "#FF4D6D", label: "→ Exit",        size: 5 },
  RETURNED_TO_FIXTURE:     { color: "#FFB800", label: "Returned",      size: 4 },
  RECEIVED_BACKROOM:       { color: "#FFA940", label: "Received",      size: 4 },
  OPS_REPLENISHED:         { color: "#FFA940", label: "Replenished",   size: 5 },
  OPS_STOCKTAKE_SCAN:      { color: "#9D7EFF", label: "Stocktake",     size: 4 },
  OPS_VM_RESET:            { color: "#9D7EFF", label: "VM Reset",      size: 4 },
};

const DEFAULT_CONFIG = { color: "#00D4FF", label: "", size: 4 };

export default function FlowDots({ events, zoneCenters, isAfterHours }: FlowDotsProps) {
  const [journeys, setJourneys] = useState<ActiveJourney[]>([]);
  const lastSeenIdRef = useRef<string | null>(null);
  const animRef = useRef<number | null>(null);

  // Process incoming events into animated journeys
  useEffect(() => {
    if (events.length === 0) return;

    // Find new events since last processed
    let startIdx = 0;
    if (lastSeenIdRef.current) {
      const idx = events.findIndex((e) => e.event_id === lastSeenIdRef.current);
      if (idx >= 0) startIdx = idx + 1;
      // If not found, process all (array was reset)
    }

    const newEvents = events.slice(startIdx);
    if (newEvents.length === 0) return;
    lastSeenIdRef.current = newEvents[newEvents.length - 1].event_id;

    const now = performance.now();
    const newJourneys: ActiveJourney[] = [];

    const zoneIds = Object.keys(zoneCenters);
    const fixtureIds = zoneIds.filter((z) => z.startsWith("F_"));

    for (const evt of newEvents) {
      if (SKIP_EVENTS.has(evt.event_type)) continue;

      // Throttle noisy events — only show 1 in N
      const throttle = THROTTLE_EVENTS[evt.event_type];
      if (throttle && Math.random() > 1 / throttle) continue;

      // Resolve effective zone_to (apply overrides for same-zone events)
      let effectiveTo = evt.zone_to;
      let effectiveFrom = evt.zone_from || "";

      // MOVED_TO_FLOOR with no source → originate from BACKROOM
      if (!effectiveFrom && evt.event_type === "MOVED_TO_FLOOR" && zoneCenters["BACKROOM"]) {
        effectiveFrom = "BACKROOM";
      }

      // If same zone, check overrides to create visible travel
      if (effectiveFrom === effectiveTo || !effectiveFrom) {
        const override = ZONE_OVERRIDES[evt.event_type];
        if (override !== undefined) {
          effectiveFrom = effectiveTo; // travel FROM current zone
          if (override === "TILL_RANDOM") {
            const tillIds = zoneIds.filter((z) => z.startsWith("TILL"));
            effectiveTo = tillIds[Math.floor(Math.random() * tillIds.length)] || "TILL_1";
          } else {
            effectiveTo = override || fixtureIds[Math.floor(Math.random() * fixtureIds.length)];
          }
        }
      }

      const to = zoneCenters[effectiveTo];
      if (!to) continue;

      const from = effectiveFrom ? zoneCenters[effectiveFrom] : null;
      const sameZone = effectiveFrom === effectiveTo;

      // Jitter to prevent overlap
      const jx = (Math.random() - 0.5) * 20;
      const jy = (Math.random() - 0.5) * 15;

      // For same-zone (pulse in place): originate from a wider offset
      // For cross-zone: use actual from position
      // For no-from: originate from nearby offset
      const fromPos = sameZone
        ? { x: to.x + (Math.random() - 0.5) * 50, y: to.y + (Math.random() - 0.5) * 40 }
        : from
          ? { x: from.x + jx, y: from.y + jy }
          : { x: to.x - 60 + jx, y: to.y - 40 + jy };

      newJourneys.push({
        id: evt.event_id || `${evt.tag_id}-${now}-${Math.random()}`,
        tagId: evt.tag_id,
        fromX: fromPos.x,
        fromY: fromPos.y,
        toX: to.x + jx * 0.5,
        toY: to.y + jy * 0.5,
        progress: 0,
        eventType: evt.event_type,
        startTime: now + Math.random() * 300,
        zoneTo: effectiveTo,
        zoneFrom: effectiveFrom,
      });
    }

    setJourneys((prev) => [...prev.slice(-(MAX_ACTIVE - newJourneys.length)), ...newJourneys]);
  }, [events, zoneCenters]);

  // Animation loop
  useEffect(() => {
    const tick = () => {
      const now = performance.now();
      setJourneys((prev) =>
        prev
          .map((j) => ({
            ...j,
            progress: (now - j.startTime) / (TRAVEL_DURATION + LINGER_DURATION),
          }))
          .filter((j) => j.progress < 1),
      );
      animRef.current = requestAnimationFrame(tick);
    };
    animRef.current = requestAnimationFrame(tick);
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, []);

  // Split progress into travel phase (0 → travelEnd) and linger phase (travelEnd → 1)
  const travelEnd = TRAVEL_DURATION / (TRAVEL_DURATION + LINGER_DURATION);

  return (
    <g>
      {journeys.map((j) => {
        const config = EVENT_CONFIG[j.eventType] || DEFAULT_CONFIG;
        const isOps = j.eventType.startsWith("OPS_");

        // Travel phase
        const travelProgress = Math.min(j.progress / travelEnd, 1);
        const eased = easeOutCubic(travelProgress);
        const x = j.fromX + (j.toX - j.fromX) * eased;
        const y = j.fromY + (j.toY - j.fromY) * eased;

        // Linger phase (pulse at destination)
        const isLingering = j.progress > travelEnd;
        const lingerProgress = isLingering ? (j.progress - travelEnd) / (1 - travelEnd) : 0;

        // Opacity: fade in → full → fade out at end of linger
        const opacity = j.progress < 0.05
          ? j.progress * 20
          : isLingering
            ? 1 - lingerProgress * 0.8
            : 1;

        const r = config.size;
        const dimFactor = isAfterHours && !isOps ? 0.3 : 1;

        return (
          <g key={j.id} opacity={opacity * dimFactor}>
            {/* Trail line while traveling */}
            {!isLingering && travelProgress > 0.05 && (
              <line
                x1={j.fromX + (j.toX - j.fromX) * Math.max(eased - 0.3, 0)}
                y1={j.fromY + (j.toY - j.fromY) * Math.max(eased - 0.3, 0)}
                x2={x}
                y2={y}
                stroke={config.color}
                strokeWidth={isOps ? 2 : 1.2}
                strokeOpacity={0.5}
                strokeLinecap="round"
                strokeDasharray={isOps ? "4 3" : "none"}
              />
            )}

            {/* Outer glow */}
            <circle
              cx={isLingering ? j.toX : x}
              cy={isLingering ? j.toY : y}
              r={r * 3}
              fill={config.color}
              opacity={0.12}
            />

            {/* Arrival ring pulse */}
            {isLingering && (
              <circle
                cx={j.toX}
                cy={j.toY}
                r={r * 2 + lingerProgress * 10}
                fill="none"
                stroke={config.color}
                strokeWidth={1}
                opacity={(1 - lingerProgress) * 0.5}
              />
            )}

            {/* Main dot */}
            <circle
              cx={isLingering ? j.toX : x}
              cy={isLingering ? j.toY : y}
              r={isLingering ? r * 1.2 : r}
              fill={config.color}
            />

            {/* Inner bright core */}
            <circle
              cx={isLingering ? j.toX : x}
              cy={isLingering ? j.toY : y}
              r={r * 0.4}
              fill="white"
              opacity={0.6}
            />

            {/* Event label (shows briefly during travel) */}
            {travelProgress > 0.3 && travelProgress < 0.95 && config.label && (
              <text
                x={(isLingering ? j.toX : x) + r + 4}
                y={(isLingering ? j.toY : y) + 3}
                fill={config.color}
                fontSize={8}
                fontWeight={600}
                opacity={0.8}
              >
                {config.label}
              </text>
            )}

            {/* Destination label on arrival */}
            {isLingering && lingerProgress < 0.5 && (
              <text
                x={j.toX + r + 4}
                y={j.toY + 3}
                fill={config.color}
                fontSize={7}
                fontWeight={500}
                opacity={(1 - lingerProgress * 2) * 0.7}
              >
                {config.label}
              </text>
            )}
          </g>
        );
      })}
    </g>
  );
}

function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}
