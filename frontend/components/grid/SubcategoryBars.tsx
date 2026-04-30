"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getSubcategoryPerformance, type SubcategoryPerf } from "@/lib/api";
import { useStore } from "@/lib/store";

const CATEGORY_COLORS: Record<string, string> = {
  Women_Western: "#E879F9",
  Women_Ethnic: "#F472B6",
  Men_Casual: "#60A5FA",
  Men_Formal: "#34D399",
  Kids: "#FBBF24",
  Accessories: "#FB923C",
};

function formatSubcat(s: string): string {
  return s.replace(/_/g, " ");
}

export default function SubcategoryBars() {
  const [data, setData] = useState<SubcategoryPerf[]>([]);
  const { gridFilter } = useStore();

  useEffect(() => {
    const params: Record<string, string> = {};
    if (gridFilter.category) params.category = gridFilter.category;
    getSubcategoryPerformance(params).then(setData).catch(console.error);
  }, [gridFilter.category]);

  if (!data.length) {
    return <div className="glass-card p-4 h-48 animate-pulse" />;
  }

  const maxPct = Math.max(...data.map((d) => d.trial_to_buy_pct));

  return (
    <div className="glass-card p-4 overflow-y-auto" style={{ maxHeight: "260px" }}>
      <h3 className="text-xs uppercase tracking-wider text-[var(--text-muted)] mb-3">
        Sub-category Conversion
      </h3>
      <div className="flex flex-col gap-1">
        {data.map((s, i) => {
          const widthPct = (s.trial_to_buy_pct / maxPct) * 100;
          const color = CATEGORY_COLORS[s.category] || "var(--accent-cyan)";
          return (
            <div key={s.sub_category} className="flex items-center gap-2">
              <span className="text-[11px] text-[var(--text-muted)] w-24 shrink-0 truncate" title={formatSubcat(s.sub_category)}>
                {formatSubcat(s.sub_category)}
              </span>
              <div className="flex-1 relative h-4 bg-[var(--bg-deep)] rounded overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${widthPct}%` }}
                  transition={{ duration: 0.5, delay: i * 0.04 }}
                  className="h-full rounded"
                  style={{ backgroundColor: color, opacity: 0.75 }}
                />
              </div>
              <span className="text-[11px] font-tabular text-[var(--text-primary)] w-10 text-right">
                {s.trial_to_buy_pct}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
