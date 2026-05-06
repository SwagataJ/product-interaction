"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getColorPerformance, type ColorPerf } from "@/lib/api";
import { useStore } from "@/lib/store";

const COLOR_MAP: Record<string, string> = {
  Navy: "#1e3a5f",
  Black: "#1a1a1a",
  White: "#e8e8e8",
  "Off-White": "#f5f0e8",
  Cream: "#f5e6c8",
  Pink: "#ec4899",
  Rust: "#b45309",
  Sage: "#84a98c",
  Indigo: "#4338ca",
  Mustard: "#ca8a04",
  "Forest Green": "#166534",
  "Dark Blue": "#1e3a8a",
  Charcoal: "#374151",
  Taupe: "#a8a29e",
  "Light Blue": "#93c5fd",
  Red: "#dc2626",
  Teal: "#0d9488",
  Maroon: "#7f1d1d",
  Olive: "#4d7c0f",
  Lavender: "#a78bfa",
  Coral: "#fb7185",
  Grey: "#6b7280",
  Beige: "#d4c5a9",
  Blush: "#fda4af",
};

export default function ColorPerformance() {
  const [data, setData] = useState<ColorPerf[]>([]);
  const { gridFilter } = useStore();

  useEffect(() => {
    const params: Record<string, string> = {};
    if (gridFilter.category) params.category = gridFilter.category;
    getColorPerformance(params).then(setData).catch(console.error);
  }, [gridFilter.category]);

  if (!data.length) {
    return <div className="glass-card p-4 h-48 animate-pulse" />;
  }

  const maxPct = Math.max(...data.map((d) => d.trial_to_buy_pct));

  return (
    <div className="glass-card p-4 overflow-y-auto" style={{ maxHeight: "260px" }}>
      <h3 className="text-xs uppercase tracking-wider text-[var(--text-muted)] mb-3">
        Trial to Buy — Color Performance
      </h3>
      <div className="flex flex-col gap-1">
        {data.map((c, i) => {
          const widthPct = (c.trial_to_buy_pct / maxPct) * 100;
          const swatch = COLOR_MAP[c.color] || "#7A8497";
          return (
            <div key={c.color} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full shrink-0 border border-white/10"
                style={{ backgroundColor: swatch }}
              />
              <span className="text-[11px] text-[var(--text-muted)] w-20 shrink-0 truncate">
                {c.color}
              </span>
              <div className="flex-1 relative h-4 bg-[var(--bg-deep)] rounded overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${widthPct}%` }}
                  transition={{ duration: 0.5, delay: i * 0.03 }}
                  className="h-full rounded"
                  style={{ backgroundColor: swatch, opacity: 0.7 }}
                />
              </div>
              <span className="text-[11px] font-tabular text-[var(--text-primary)] w-10 text-right">
                {c.trial_to_buy_pct}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
