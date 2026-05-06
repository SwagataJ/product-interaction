"use client";

import { useEffect, useState } from "react";
import { getSizeRejectionHeatmap, type SizeRejection } from "@/lib/api";
import { useStore } from "@/lib/store";

function getHeatColor(pct: number): string {
  if (pct >= 80) return "var(--heat-hot)";
  if (pct >= 60) return "var(--accent-coral)";
  if (pct >= 40) return "var(--heat-warm)";
  if (pct >= 20) return "var(--accent-amber)";
  return "var(--heat-cold)";
}

export default function SizeRejectionHeatmap() {
  const [data, setData] = useState<SizeRejection[]>([]);
  const { gridFilter } = useStore();

  useEffect(() => {
    const params: Record<string, string> = {};
    if (gridFilter.category) params.category = gridFilter.category;
    if (gridFilter.sku) params.sku = gridFilter.sku;
    getSizeRejectionHeatmap(params).then(setData).catch(console.error);
  }, [gridFilter]);

  if (!data.length) return <div className="glass-card p-4 h-48 animate-pulse" />;

  return (
    <div className="glass-card p-4">
      <h3 className="text-xs uppercase tracking-wider text-[var(--text-muted)] mb-3">
        Trial to Buy — Rejection Rate by Size
      </h3>
      <div className="grid grid-cols-5 gap-1.5">
        {data.map((d) => (
          <div
            key={d.size}
            className="relative flex flex-col items-center justify-center rounded-md p-2 transition-all hover:scale-105"
            style={{
              backgroundColor: getHeatColor(d.rejection_pct),
              opacity: 0.85,
            }}
            title={`${d.size}: ${d.rejection_pct}% rejection (${d.rejected}/${d.total_trials})`}
          >
            <span className="text-xs font-bold text-white">{d.size}</span>
            <span className="text-[10px] font-tabular text-white/80">
              {d.rejection_pct}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
