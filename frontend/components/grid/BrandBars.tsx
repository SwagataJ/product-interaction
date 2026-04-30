"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getBrandPerformance, type BrandPerf } from "@/lib/api";
import { useStore } from "@/lib/store";

const CATEGORY_COLORS: Record<string, string> = {
  Women_Western: "#E879F9",
  Women_Ethnic: "#F472B6",
  Men_Casual: "#60A5FA",
  Men_Formal: "#34D399",
  Kids: "#FBBF24",
  Accessories: "#FB923C",
};

export default function BrandBars() {
  const [data, setData] = useState<BrandPerf[]>([]);
  const { gridFilter } = useStore();

  useEffect(() => {
    const params: Record<string, string> = {};
    if (gridFilter.category) params.category = gridFilter.category;
    getBrandPerformance(params).then(setData).catch(console.error);
  }, [gridFilter.category]);

  if (!data.length) {
    return <div className="glass-card p-4 h-48 animate-pulse" />;
  }

  const maxPct = Math.max(...data.map((d) => d.trial_to_buy_pct));

  return (
    <div className="glass-card p-4 overflow-y-auto" style={{ maxHeight: "260px" }}>
      <h3 className="text-xs uppercase tracking-wider text-[var(--text-muted)] mb-3">
        Brand Conversion
      </h3>
      <div className="flex flex-col gap-1">
        {data.map((b, i) => {
          const widthPct = (b.trial_to_buy_pct / maxPct) * 100;
          const color = CATEGORY_COLORS[b.category] || "var(--accent-cyan)";
          return (
            <div key={b.brand} className="flex items-center gap-2">
              <span className="text-[11px] text-[var(--text-muted)] w-24 shrink-0 truncate">
                {b.brand}
              </span>
              <div className="flex-1 relative h-4 bg-[var(--bg-deep)] rounded overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${widthPct}%` }}
                  transition={{ duration: 0.5, delay: i * 0.05 }}
                  className="h-full rounded"
                  style={{ backgroundColor: color, opacity: 0.75 }}
                />
              </div>
              <span className="text-[11px] font-tabular text-[var(--text-primary)] w-10 text-right">
                {b.trial_to_buy_pct}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
