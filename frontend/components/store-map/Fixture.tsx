"use client";

import { useStore } from "@/lib/store";

interface FixtureProps {
  zone: {
    id: string;
    x: number;
    y: number;
    w: number;
    h: number;
    label: string;
    category?: string;
    placement?: string;
  };
  heatValue: number;
  maxHeat: number;
  isHighlighted: boolean;
}

const CATEGORY_COLORS: Record<string, string> = {
  Women_Western: "#E879F9",
  Women_Ethnic: "#F472B6",
  Men_Casual: "#60A5FA",
  Men_Formal: "#34D399",
  Kids: "#FBBF24",
  Accessories: "#FB923C",
};

function heatColor(value: number, max: number): string {
  const t = Math.min(Math.max(value / Math.max(max, 1), 0), 1);
  // Interpolate from deep blue to warm orange/red
  const r = Math.round(27 + t * 228);
  const g = Math.round(51 + t * (122 - 51) * (1 - t) - t * 51);
  const b = Math.round(88 - t * 50);
  return `rgb(${r}, ${g}, ${b})`;
}

export default function Fixture({ zone, heatValue, maxHeat, isHighlighted }: FixtureProps) {
  const { setChatOpen, setChatPendingContext } = useStore();
  const catColor = CATEGORY_COLORS[zone.category || ""] || "#60A5FA";

  const handleClick = () => {
    setChatOpen(true);
    setChatPendingContext(`Analyze fixture ${zone.id} (${zone.label}). What's its performance and how does it compare to others?`);
  };

  const shortLabel = zone.label.split("(")[0].trim();
  const brandLabel = zone.label.match(/\(([^)]+)\)/)?.[1] || "";

  return (
    <g onClick={handleClick} className="cursor-pointer" role="button" tabIndex={0}>
      {/* Highlight glow ring */}
      {isHighlighted && (
        <>
          <rect
            x={zone.x - 4}
            y={zone.y - 4}
            width={zone.w + 8}
            height={zone.h + 8}
            rx={10}
            fill="none"
            stroke="var(--accent-cyan)"
            strokeWidth={2}
            opacity={0.6}
            filter="url(#glow)"
          >
            <animate attributeName="opacity" values="0.3;0.8;0.3" dur="2s" repeatCount="indefinite" />
          </rect>
        </>
      )}

      {/* Main fixture rect */}
      <rect
        x={zone.x}
        y={zone.y}
        width={zone.w}
        height={zone.h}
        rx={6}
        fill={heatColor(heatValue, maxHeat)}
        fillOpacity={0.7}
        stroke={isHighlighted ? "var(--accent-cyan)" : catColor}
        strokeWidth={isHighlighted ? 2 : 1}
        strokeOpacity={isHighlighted ? 1 : 0.4}
      />

      {/* Category accent bar at top */}
      <rect
        x={zone.x + 1}
        y={zone.y + 1}
        width={zone.w - 2}
        height={3}
        rx={1}
        fill={catColor}
        fillOpacity={0.7}
      />

      {/* Placement badge */}
      {zone.placement && (
        <g>
          <rect
            x={zone.x + zone.w - 28}
            y={zone.y + zone.h - 14}
            width={24}
            height={11}
            rx={3}
            fill="rgba(0,0,0,0.4)"
          />
          <text
            x={zone.x + zone.w - 16}
            y={zone.y + zone.h - 6}
            textAnchor="middle"
            dominantBaseline="central"
            fill={catColor}
            fontSize={6}
            fontWeight={600}
            opacity={0.8}
          >
            {zone.placement === "front" ? "FRONT" :
             zone.placement === "back" ? "BACK" :
             zone.placement === "mid" ? "MID" :
             zone.placement === "near_exit" ? "EXIT" :
             zone.placement === "side" ? "SIDE" : zone.placement.toUpperCase()}
          </text>
        </g>
      )}

      {/* Category label */}
      <text
        x={zone.x + zone.w / 2}
        y={zone.y + zone.h / 2 - 6}
        textAnchor="middle"
        dominantBaseline="central"
        fill="#E8ECF1"
        fontSize={8}
        fontWeight={600}
      >
        {shortLabel.length > 16 ? shortLabel.slice(0, 14) + "..." : shortLabel}
      </text>

      {/* Brand label */}
      {brandLabel && (
        <text
          x={zone.x + zone.w / 2}
          y={zone.y + zone.h / 2 + 5}
          textAnchor="middle"
          dominantBaseline="central"
          fill="#7A8497"
          fontSize={6}
        >
          {brandLabel.length > 20 ? brandLabel.slice(0, 18) + "..." : brandLabel}
        </text>
      )}

      {/* Heat metric */}
      <text
        x={zone.x + zone.w / 2}
        y={zone.y + zone.h / 2 + 17}
        textAnchor="middle"
        dominantBaseline="central"
        fill={catColor}
        fontSize={8}
        fontWeight={700}
        fontFamily="var(--font-geist-mono), monospace"
      >
        {heatValue > 0 ? `${heatValue.toFixed(1)}` : "-"}
      </text>

      {/* Hover effect overlay */}
      <rect
        x={zone.x}
        y={zone.y}
        width={zone.w}
        height={zone.h}
        rx={6}
        fill="white"
        fillOpacity={0}
        className="hover:fill-opacity-[0.05] transition-all duration-200"
      />
    </g>
  );
}
